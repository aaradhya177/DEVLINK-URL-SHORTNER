# Architecture Decision Record: Distributed Link Intelligence Platform

## Status

Accepted for initial implementation.

## Context

We are building a production-grade URL shortener with analytics, operational reliability, and a roadmap beyond a TinyURL-style clone. This document is the source of truth for the initial monorepo scaffold and high-level implementation direction.

## Assumptions

- The first production target is a horizontally scalable web/API deployment backed by managed PostgreSQL, Redis, and Kafka-compatible infrastructure.
- Local development should be runnable on one machine with Docker Compose for shared dependencies only.
- The API and redirect path start in one FastAPI service, with code organized so the redirect hot path can be split into a dedicated service later if traffic requires it.
- Authentication will be added after core anonymous link creation and redirect behavior are working.
- Analytics events are eventually consistent; redirect latency must not depend on analytics writes.
- Kafka is the preferred event bus. RabbitMQ remains a fallback only if Kafka becomes too heavy for a target environment.

## High-Level Architecture

```text
                         +----------------------+
                         |  React + TypeScript  |
                         |  Frontend (apps/web) |
                         +----------+-----------+
                                    |
                                    | HTTPS JSON API
                                    v
                         +----------------------+
                         | FastAPI API Service  |
                         | apps/api             |
                         | - link CRUD          |
                         | - auth (future)      |
                         | - redirect endpoint  |
                         +----+------------+----+
                              |            |
                primary data  |            | cache/rate limits
                              v            v
                       +------+---+    +---+------+
                       |PostgreSQL|    |  Redis   |
                       +------+---+    +---+------+
                              |
                              | async click event publish
                              v
                       +------+------+
                       |   Kafka     |
                       +------+------+
                              |
                              | consume analytics events
                              v
                  +-----------+------------+
                  | Analytics Worker       |
                  | apps/analytics-worker  |
                  | - aggregate clicks     |
                  | - enrich events        |
                  | - persist rollups      |
                  +-----------+------------+
                              |
                              v
                       +------+---+
                       |PostgreSQL|
                       +----------+
```

### Components

- **API service:** FastAPI application responsible for link CRUD, health checks, auth once added, and publishing analytics events.
- **Redirect hot path:** Initially implemented in the API service as a dedicated endpoint optimized for low latency. It should read from Redis first, fall back to PostgreSQL, publish analytics asynchronously, and return redirects quickly.
- **Analytics worker:** Python service that consumes click events from Kafka and writes normalized events and aggregate rollups to PostgreSQL.
- **Frontend:** React + TypeScript app for link management, dashboards, and account workflows.
- **Infrastructure:** Docker Compose for local PostgreSQL, Redis, and Kafka. Application services are run directly during local development.

## Tech Stack Decisions

- **Backend:** FastAPI with Python. FastAPI provides high-performance async request handling, OpenAPI generation, type-driven validation through Pydantic, and a mature ecosystem.
- **Primary storage:** PostgreSQL. It provides relational integrity, transactional link management, indexing, JSON support for metadata, and strong operational familiarity.
- **Cache and rate limiting:** Redis. It is suitable for short-code lookups, TTL-based caching, counters, distributed locks, and sliding-window or token-bucket rate limiting.
- **Async event processing:** Kafka. Click events are append-heavy and analytics consumers may evolve independently. Kafka gives durable ordered partitions and replay capability. For local development we use a single-node KRaft Kafka container to avoid ZooKeeper. RabbitMQ is a fallback only if a deployment environment cannot support Kafka.
- **Frontend:** React + TypeScript with Vite. This keeps the client fast to develop, strongly typed, and easy to evolve into a dashboard-heavy product.
- **Python dependency management:** Poetry. It keeps dependency metadata, project scripts, virtualenv workflows, and packaging configuration in `pyproject.toml`, which matches the monorepo goal of independently runnable apps.

## ID Generation Strategy

Short links use a Snowflake-style numeric ID encoded with Base62.

### Snowflake-Style ID Layout

The generated integer is composed from time and machine-local sequence fields:

```text
| timestamp milliseconds since custom epoch | worker id | sequence |
```

- **Timestamp:** Monotonic millisecond timestamp relative to a custom epoch. This keeps IDs roughly sortable by creation time.
- **Worker ID:** Identifies the API instance or ID generator node. In local development this can default to `1`; production must assign stable unique worker IDs.
- **Sequence:** Incremented per millisecond for IDs generated on the same worker. If the sequence overflows within the same millisecond, generation waits for the next millisecond.

### Base62 Encoding

The integer ID is encoded using Base62 characters:

```text
0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz
```

Base62 keeps codes URL-safe, compact, case-sensitive, and free of punctuation. The database stores both the numeric ID and the generated short code. A unique index on `short_code` protects against implementation or configuration mistakes.

## Core Database Schema Design

No migrations are included in the initial scaffold. The intended schema is:

### `users`

- `id`: UUID primary key.
- `email`: unique, indexed, case-normalized.
- `password_hash`: nullable until auth is implemented.
- `created_at`, `updated_at`.
- Relationship: one user has many links.

### `links`

- `id`: bigint primary key generated by Snowflake-style generator.
- `owner_id`: nullable foreign key to `users.id` for anonymous or pre-auth links.
- `short_code`: unique, indexed, non-null.
- `destination_url`: non-null.
- `title`: nullable display name.
- `is_active`: boolean, indexed.
- `expires_at`: nullable, indexed.
- `created_at`, `updated_at`.
- Indexes: unique `short_code`; composite `(owner_id, created_at DESC)`; partial or composite index for active, unexpired redirects.

### `click_events`

- `id`: UUID primary key.
- `link_id`: foreign key to `links.id`, indexed.
- `occurred_at`: timestamp, indexed.
- `ip_hash`: privacy-preserving hash of IP address.
- `user_agent`: raw or parsed user agent string.
- `referer`: nullable.
- `country`, `region`, `city`: nullable enrichment fields.
- `device_type`, `browser`, `os`: nullable parsed fields.
- Indexes: `(link_id, occurred_at DESC)` and time-based index for retention jobs.

### `link_daily_stats`

- `link_id`: foreign key to `links.id`.
- `stat_date`: date.
- `click_count`: integer.
- Optional dimension columns such as `country`, `device_type`, or `referer_domain`.
- Primary key: `(link_id, stat_date)` for simple daily totals, or expanded composite key if dimensions are included.

### `api_keys` (future)

- `id`: UUID primary key.
- `user_id`: foreign key to `users.id`.
- `key_hash`: unique, indexed.
- `name`, `last_used_at`, `created_at`, `revoked_at`.

## API Surface Overview

- `GET /health` - service health check.
- `POST /api/v1/links` - create a short link.
- `GET /api/v1/links` - list links for current user.
- `GET /api/v1/links/{short_code}` - get link details.
- `PATCH /api/v1/links/{short_code}` - update link metadata or destination.
- `DELETE /api/v1/links/{short_code}` - deactivate or delete a link.
- `GET /{short_code}` - redirect hot path.
- `GET /api/v1/links/{short_code}/analytics` - retrieve analytics summary.
- `POST /api/v1/auth/register` - future user registration.
- `POST /api/v1/auth/login` - future login.
- `POST /api/v1/auth/refresh` - future token refresh.

## Monorepo Folder Structure

```text
.
+-- apps
|   +-- api
|   |   +-- app
|   |   |   +-- api
|   |   |   |   +-- v1
|   |   |   +-- core
|   |   |   +-- main.py
|   |   +-- tests
|   |   +-- .env.example
|   |   +-- pyproject.toml
|   +-- analytics-worker
|   |   +-- worker
|   |   |   +-- worker.py
|   |   +-- tests
|   |   +-- pyproject.toml
|   +-- web
|       +-- src
|       |   +-- pages
|       |   +-- routes
|       |   +-- styles
|       |   +-- App.tsx
|       |   +-- main.tsx
|       +-- index.html
|       +-- package.json
|       +-- tsconfig.json
|       +-- tsconfig.node.json
|       +-- vite.config.ts
|       +-- .env.example
+-- docs
|   +-- ARCHITECTURE.md
+-- infra
|   +-- docker-compose.yml
+-- .gitignore
+-- README.md
```

## Coding Standards

### Python

- Follow PEP 8.
- Use type hints for public functions and meaningful internal boundaries.
- Format with Black and lint with Ruff.
- Use Pydantic settings/models for environment-driven configuration.
- Prefer dependency injection boundaries for database, cache, event producer, and auth services.

### TypeScript

- Enable TypeScript strict mode.
- Use ESLint and Prettier.
- Keep route components small and move shared UI or API client code into dedicated modules as the app grows.
- Avoid unchecked `any`; prefer typed API contracts.

### Commit Messages

Use Conventional Commits:

- `feat: add link creation endpoint`
- `fix: prevent expired link redirects`
- `docs: update architecture roadmap`
- `test: add redirect cache integration test`
- `chore: update local compose services`

### Testing Philosophy

- Unit tests for pure business logic, ID generation, Base62 encoding, validation, and UI components.
- Integration tests for API/database behavior, Redis caching, Kafka publishing/consuming, and redirect behavior.
- Target coverage: at least 80% line coverage for backend and worker code, with higher coverage around ID generation and redirect logic.
- Frontend coverage should focus on route behavior, form validation, API client states, and dashboard rendering.

## Phased Build Roadmap

1. **Core link CRUD:** Implement link model, migrations, repository layer, create/list/read/update/delete endpoints, and validation.
2. **Redirect engine:** Add `GET /{short_code}`, expiration handling, active-state checks, and redirect response behavior.
3. **Auth:** Add users, password hashing or external identity provider integration, JWT access/refresh tokens, and owner-scoped link access.
4. **Caching:** Add Redis short-code cache, cache invalidation on link updates, and API/redirect rate limiting.
5. **Analytics pipeline:** Publish click events to Kafka, consume in analytics worker, persist raw events, and maintain rollups.
6. **Frontend:** Build link creation, link list, edit/deactivate flows, auth screens, and analytics dashboard.
7. **Advanced features:** Custom aliases, QR codes, branded domains, UTM builder, webhook notifications, API keys, and team workspaces.
8. **Hardening:** Add observability, structured logs, metrics, tracing, security headers, abuse detection, privacy controls, backups, and retention jobs.
9. **Deployment:** Containerize apps, provision managed services, configure CI/CD, run migrations, add health/readiness checks, and document runbooks.
