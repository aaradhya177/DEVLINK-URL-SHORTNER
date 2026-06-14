# DEVLINK Architecture

DEVLINK is a production-oriented URL shortener with authenticated link
management, Redis-backed redirect caching, asynchronous click analytics, and a
React dashboard.

This document reflects the current implementation. The original Phase 0 plan
evolved as features were built; deviations are called out near the end.

## System Overview

```text
Browser
  |
  | React app, JSON API, redirects
  v
+-------------------+        +-------------------+
| apps/web          |        | apps/api          |
| React + Vite      |------->| FastAPI           |
| dashboard UI      |        | auth, links, RBAC |
+-------------------+        | redirect, metrics |
                             +----+-----+----+---+
                                  |     |    |
                         Postgres |     |    | Redis cache/rate limits
                                  v     |    v
                           +------+--+  | +--+------+
                           | Postgres|  | | Redis   |
                           +------+--+  | +---------+
                                  ^     |
                                  |     | Kafka click event
                                  |     v
                            +-----+-----+---------+
                            | apps/analytics-worker|
                            | consume, enrich,     |
                            | aggregate clicks     |
                            +----------------------+
```

## Applications

- `apps/api`: FastAPI service. It owns authentication, link CRUD, workspace
  RBAC, public redirects, QR code generation, analytics read APIs, URL safety
  checks, rate limiting, structured logs, and Prometheus `/metrics`.
- `apps/analytics-worker`: async Python worker. It consumes click events,
  enriches them with GeoIP/user-agent parsing, writes raw event rows, and updates
  daily aggregates idempotently.
- `apps/web`: React + TypeScript Vite app. It handles auth, link dashboard,
  bulk shortening, QR preview, and analytics charts.
- `infra`: Docker Compose, production-like Compose, Terraform for AWS ECS/RDS/
  Redis/ALB, GitHub Actions CI/CD, and deployment scripts.

## API Surface

The API exposes:

- `GET /health`
- `GET /metrics` for internal Prometheus scraping
- `/api/v1/auth/*` for register/login/refresh/logout and Google OAuth stubs
- `/api/v1/links/*` for link CRUD, bulk creation, and QR images
- `/api/v1/workspaces/*` for workspace and member management
- `/api/v1/analytics/{link_id}/*` for dashboard analytics
- `/r/{short_code}` and `/r/{short_code}/verify` for public redirects

The generated OpenAPI spec is checked in at `docs/api-spec.yaml`.

## Data Model

Implemented PostgreSQL tables:

- `users`: UUID primary key, normalized unique email, password hash, timestamps.
- `refresh_tokens`: hashed refresh tokens with expiry/revocation metadata.
- `workspaces`: workspace owner and timestamps.
- `workspace_members`: role membership with `owner`, `admin`, `editor`,
  `viewer`.
- `links`: Snowflake-style bigint ID, Base62 `short_code`, owner/workspace,
  destination URL, `long_url_hash`, password hash, active/expiration flags,
  safety metadata, denormalized `click_count`, timestamps.
- `click_events`: range-partitioned by `clicked_at`, keyed by `(id, clicked_at)`,
  stores privacy-preserving IP hash, parsed geo/device fields, referrer domain,
  and metadata JSON.
- `link_analytics_daily`: aggregate rollups by link/date/country/device/browser/
  OS/referrer domain.

Important indexes include:

- Unique `links.short_code` for redirect lookup.
- `links.long_url_hash` for deduplication.
- Link listing indexes by owner/workspace/created time and expiration filters.
- `click_events(link_id, clicked_at)` for event access and retention.
- `link_analytics_daily` composite primary key for idempotent aggregate upserts.

## Redirect Hot Path

Redirect flow:

1. Apply Redis redirect rate limit.
2. Lookup `link:{short_code}` in Redis.
3. On miss, query PostgreSQL and populate Redis with TTL bounded by expiration.
4. Reject inactive/expired/flagged links.
5. For password-protected links, require a short-lived signed redirect token.
6. Log redirect timing and publish a click event in a background task.
7. Return `307 Temporary Redirect`.

The redirect handler does not wait for analytics database writes.

## ID Generation

Links use a Snowflake-style 64-bit integer:

```text
timestamp milliseconds since custom epoch | worker id | sequence
```

The integer is Base62-encoded into the public short code. This gives compact,
URL-safe, mostly time-sortable IDs without a central database sequence on the
hot creation path. The worker ID is currently environment-driven.

## Caching And Rate Limiting

Redis is used for:

- `short_code -> link metadata` cache.
- QR code image cache.
- Redirect abuse limits.
- Password verification attempt limits.
- Application-level read/write/bulk API limits.

Link updates, deletes, expiration jobs, and URL safety flagging invalidate
affected redirect cache entries.

## Analytics Pipeline

Redirects publish click events to Kafka with:

- `event_id` for idempotency.
- `correlation_id` for log tracing.
- `link_id`, timestamp, coarse anonymized IP, user-agent, referrer.

The worker commits Kafka offsets only after malformed messages are skipped or
database writes commit. Raw click event insertion uses conflict handling; daily
aggregates and `links.click_count` are incremented only when the raw insert is
new. Duplicate delivery therefore does not double-count analytics.

Privacy choices:

- Raw IPs are not persisted.
- IPs are hashed with a daily salt before storage.
- Referrers are reduced to domains.
- Full user-agent strings are parsed, then omitted from persistence.

## Auth And Authorization

Auth uses password login plus JWT access/refresh tokens:

- Access tokens are short-lived.
- Refresh tokens are rotated and stored hashed for revocation/reuse prevention.
- Password hashes use Passlib bcrypt.
- Protected endpoints use FastAPI dependencies for current-user lookup.

Workspace RBAC supports `owner > admin > editor > viewer`. Link access is allowed
for link owners or users with sufficient workspace membership.

## URL Safety And Expiration

URL creation validates HTTP(S) URLs and rejects localhost/private-network targets
unless explicitly allowed for local development.

Google Safe Browsing is implemented behind a mockable provider interface. Link
creation fails open with a tight timeout to preserve latency; pending checks are
retried by maintenance jobs. Flagged links are marked inactive, given a
`flagged_reason`, and removed from cache.

Expiration maintenance marks expired links inactive and invalidates cache. Jobs
use `FOR UPDATE SKIP LOCKED` to stay safe under multiple workers.

## Observability

Implemented:

- JSON logs for API and worker with timestamp, level, service, logger, message,
  correlation ID, event ID, and link ID where relevant.
- Correlation ID middleware propagates `X-Correlation-ID` / `X-Request-ID`.
- API Prometheus `/metrics`.
- Worker Prometheus metrics on port `9101`.
- Terraform CloudWatch log groups, Container Insights, dashboard, and alarms.

See `docs/MONITORING.md`.

## Deployment

Local development:

- `infra/docker-compose.yml` starts Postgres, Redis, Kafka.
- API, worker, and web can run directly.

Production simulation:

- `infra/docker-compose.prod.yml` builds API, worker, web, Postgres, Redis,
  Kafka, and nginx.

AWS path:

- Terraform provisions VPC, ALB, ECS Fargate services, RDS Postgres,
  ElastiCache Redis, CloudWatch logs/alarms, and a low-cost Kafka-compatible
  broker task.
- GitHub Actions builds images, pushes to GHCR, and updates ECS services.

See `docs/DEPLOYMENT.md`.

## Testing

Implemented test coverage includes:

- Unit tests for ID generation, URL normalization/safety, auth security, rate
  limiting, redirect service behavior, maintenance jobs, and schema validation.
- Integration tests for auth/workspaces, links, and redirects when
  `TEST_DATABASE_URL` is configured.
- Worker idempotency integration test when a test database is configured.
- Frontend Vitest/React Testing Library tests for link creation and analytics UI.

CI runs lint/type-check/test gates and enforces configured coverage thresholds.

## Deviations From The Original Plan

- Auth, workspaces, analytics, URL safety, observability, and deployment were
  implemented earlier than the original scaffold-only architecture described.
- The public redirect path is `/r/{short_code}` instead of root `/{short_code}`
  to avoid collisions with frontend routes and API docs.
- The AWS minimal deployment uses a single lightweight Kafka-compatible ECS task
  instead of MSK because MSK is expensive for a solo portfolio project. MSK
  remains the scale-up recommendation.
- ECS tasks in the minimal Terraform path use public IPs behind security groups
  to avoid NAT Gateway cost. A production-scale deployment should move tasks to
  private subnets with NAT or VPC endpoints.
- Google OAuth endpoints are documented stubs because real OAuth requires client
  credentials and callback configuration.
- Unique click counting is intentionally not implemented yet; analytics reports
  total clicks and documents the limitation.
