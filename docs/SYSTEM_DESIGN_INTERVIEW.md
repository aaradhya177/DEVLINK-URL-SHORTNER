# DEVLINK System Design Interview Walkthrough

This document is written as a standalone interview guide for explaining DEVLINK
without reading the code.

## 1. Problem Statement

Design a production-grade URL shortener with:

- Short link creation with optional custom aliases.
- Authenticated dashboard for managing links.
- Public redirect endpoint with low latency.
- Password-protected and expiring links.
- Click analytics by time, geography, device, browser, and OS.
- Workspace/team access control.
- Abuse controls, malicious URL checks, observability, CI/CD, and deployment.

## 2. Requirements

Functional requirements:

- Register, log in, refresh tokens, and log out.
- Create, list, update, and soft-delete links.
- Deduplicate repeated URLs by normalized URL hash.
- Support custom aliases and alias collision handling.
- Redirect active links quickly.
- Block expired, inactive, flagged, or unverified password-protected links.
- Publish click events asynchronously.
- Aggregate click analytics for dashboards.
- Manage workspaces and workspace members with RBAC.
- Generate QR codes for short links.

Non-functional requirements:

- Redirect p95 should stay low; analytics must not block redirects.
- Link creation should remain available even if external URL safety checks are
  slow.
- Duplicate click event delivery must not double-count analytics.
- Raw IPs should not be persisted.
- API errors and click events should be traceable with correlation IDs.
- The system should be deployable locally and to cloud infrastructure.

## 3. Back-Of-Envelope Capacity

Assume a successful product:

- 1 million registered users.
- 10 million links.
- 100 million redirects/day.
- 10 million analytics dashboard reads/day.
- Average destination URL: 120 bytes; metadata row roughly 1 KB.
- Average raw click event after enrichment: 500-1000 bytes.

Redirect throughput:

```text
100M redirects/day / 86,400 seconds ~= 1,160 redirects/second average
Peak at 10x average ~= 11,600 redirects/second
```

Click event storage:

```text
100M events/day * ~800 bytes ~= 80 GB/day raw before indexes/overhead
30 days ~= 2.4 TB raw event data
```

Aggregate storage is much smaller. If each link has a few countries/devices per
day, daily rollups are usually millions of rows/day, not hundreds of millions.

Implication:

- Redirect lookup must use cache.
- Click events need partitioning and retention.
- Dashboard reads should use aggregate tables, never raw click events.
- The event bus must buffer worker outages.

## 4. API Design Summary

Main endpoints:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/links`
- `POST /api/v1/links/bulk`
- `GET /api/v1/links`
- `PATCH /api/v1/links/{link_id}`
- `DELETE /api/v1/links/{link_id}`
- `GET /r/{short_code}`
- `POST /r/{short_code}/verify`
- `GET /api/v1/analytics/{link_id}/summary`
- `GET /api/v1/analytics/{link_id}/timeseries`
- `GET /api/v1/analytics/{link_id}/geo`
- `GET /api/v1/analytics/{link_id}/devices`

The generated OpenAPI spec is `docs/api-spec.yaml`.

## 5. Data Model

Core tables:

- `users`: identity and password hash.
- `refresh_tokens`: hashed refresh tokens for rotation and revocation.
- `workspaces`: team containers.
- `workspace_members`: RBAC roles.
- `links`: short-code metadata and redirect controls.
- `click_events`: raw event table partitioned by month.
- `link_analytics_daily`: pre-aggregated dashboard facts.

Indexes are chosen around hot paths:

- `links.short_code` unique index for redirect lookup.
- `links.long_url_hash` for deduplication.
- Owner/workspace listing indexes for dashboards.
- Expiration/active indexes for maintenance jobs.
- `click_events(link_id, clicked_at)` for event access/retention.
- Composite aggregate primary key for idempotent upserts.

## 6. ID Generation

DEVLINK uses a Snowflake-style 64-bit integer:

```text
timestamp | worker id | sequence
```

Then it Base62-encodes the integer into the public short code.

Why:

- No database round trip required for ID generation.
- IDs are compact and URL-safe.
- IDs are roughly ordered by creation time.
- Sequence bits handle high throughput inside one millisecond.

Tradeoff:

- Workers need unique worker IDs. Today this is environment-driven; at larger
  scale it should be coordinated by deployment config or a service registry.

## 7. Redirect Caching

Redirects use cache-aside Redis:

1. Try `link:{short_code}`.
2. On miss, read Postgres.
3. Cache metadata with TTL bounded by link expiration.
4. Invalidate cache on update/delete/flag/expiration.

Cached metadata includes destination URL, active state, expiration, workspace ID,
and password protection metadata.

Why:

- Redirects are read-heavy.
- Hot links may receive thousands of hits/second.
- Postgres should not be the first hop for every redirect.

Future scale improvement:

- Add in-process L1 cache for viral links.
- Add CDN/edge redirect workers for global latency.

## 8. Analytics Pipeline

Redirects publish click events asynchronously to Kafka. The worker consumes,
enriches, and writes:

1. Insert raw `click_events` row with `event_id`.
2. If insert succeeds, upsert daily aggregate.
3. Increment `links.click_count`.
4. Commit Kafka offset.

Why event-driven:

- Redirect latency does not depend on analytics writes.
- Kafka buffers worker/database outages.
- Events can be replayed if aggregation logic changes.
- More consumers can be added later.

Tradeoff:

- Analytics are eventually consistent. A click may redirect successfully before
  it appears in the dashboard.

Idempotency:

- `event_id` prevents raw duplicate inserts.
- Aggregates increment only after a new raw insert.
- Duplicate Kafka delivery does not double-count.

## 9. Security And Privacy

Implemented choices:

- JWT access tokens plus refresh token rotation.
- Refresh tokens stored hashed.
- Bcrypt password hashing.
- FastAPI dependencies enforce auth and RBAC.
- Pydantic models reject unexpected fields.
- Redirect URLs reject non-HTTP schemes, localhost, and private IP ranges by
  default.
- Raw IPs are never persisted.
- Referrers are reduced to domains.
- Password-protected redirect verification is rate-limited.
- Security headers and restrictive CORS are configured.

## 10. Observability

Signals:

- API request metrics and status codes at `/metrics`.
- Redirect timing logs: cache lookup, DB fallback, total response time.
- Worker metrics: processed events, duplicate events, malformed events,
  processing latency, consumer lag.
- CloudWatch alarms: API 5xx, unhealthy ECS targets, RDS CPU/connections, ECS
  CPU.
- JSON logs include `correlation_id` and `event_id`.

## 11. Tradeoffs Made

- Single FastAPI service owns both API and redirect path. This is simpler now;
  split redirect into a dedicated service if redirect traffic dominates.
- Kafka is represented by a small broker for local/minimal AWS deployments. MSK
  is better operationally at scale but costly.
- Analytics are daily aggregates, not real-time per-second streams.
- Unique clicks are not implemented yet because strong privacy constraints make
  uniqueness non-trivial.
- AWS minimal deployment avoids NAT Gateway to control cost.
- Google OAuth is stubbed until credentials and callback domains exist.

## 12. 10x Scale Plan

At 10x traffic:

- Split redirect service from management API.
- Add autoscaling for API, redirect, and worker tasks.
- Tune Redis memory and add replication.
- Add topic partitioning strategy by `link_id`.
- Add retention policies for raw click events.
- Add CloudFront or edge redirect caching for popular links.
- Add read replicas for analytics/dashboard queries if Postgres saturates.

## 13. 100x Scale Plan

At 100x traffic:

- Use a dedicated globally distributed redirect service.
- Move click events to managed Kafka/MSK or Kinesis with formal retention.
- Partition raw event storage by month/day and consider S3 lakehouse archival.
- Use approximate unique counting with HyperLogLog or privacy-preserving
  rotating visitor keys.
- Serve redirects at the edge for stable destinations.
- Introduce multi-region active/active or active/passive deployment.
- Add WAF, bot detection, abuse scoring, and automated malicious link takedown.
- Use blue/green or canary deployments with automatic rollback.

## 14. Interview Closing Summary

The key design is separating redirect latency from analytics durability:

- Redis and indexed Postgres make redirects fast.
- Kafka makes click analytics asynchronous and replayable.
- Idempotent worker writes make duplicate delivery safe.
- Aggregate tables make dashboards cheap.
- Observability and runbooks make the system explainable in production.
