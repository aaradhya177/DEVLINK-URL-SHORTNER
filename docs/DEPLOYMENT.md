# Deployment Notes

This is a seed deployment checklist for the production hardening phase.

## Required Secrets And Environment

Production deployments must provide these values from a secret manager or
deployment environment, never from committed files:

- `DATABASE_URL`: PostgreSQL async SQLAlchemy URL. Use a least-privileged app
  role and TLS where the provider supports it.
- `REDIS_URL`: Redis URL. Use authentication/TLS in managed or shared networks.
- `KAFKA_BROKERS`: Kafka broker list for click-event publishing.
- `JWT_SECRET`: at least 32 random bytes, unique per environment.
- `JWT_ALGORITHM`: keep one of `HS256`, `HS384`, or `HS512`.
- `GOOGLE_SAFE_BROWSING_API_KEY`: optional but recommended for malicious URL
  detection.
- `CORS_ALLOWED_ORIGINS`: comma-separated production frontend origins. Do not
  use `*`.

Operational tuning:

- `DB_POOL_SIZE`
- `DB_MAX_OVERFLOW`
- `DB_POOL_TIMEOUT_SECONDS`
- `REDIS_MAX_CONNECTIONS`
- `RATE_LIMIT_*`
- `REDIRECT_PASSWORD_ATTEMPT_LIMIT`
- `REDIRECT_PASSWORD_ATTEMPT_WINDOW_SECONDS`

Security-sensitive defaults:

- `APP_ENV=production` enables HSTS headers.
- `ALLOW_PRIVATE_REDIRECT_URLS=false` should remain false in production.
- `.env.example` is for local development shape only; production values must be
  injected securely.

## Dependency Audit Commands

Frontend:

```text
cd apps/web
npm audit --audit-level=high
```

Python direct dependency audit until Poetry lock files are introduced:

```text
pip-audit -r <pinned-project-requirements.txt> --no-deps
```

Full lock-file audits should replace the temporary pinned-requirements approach
once Phase 13 adds reproducible lock files for the API and worker.

## Production-Like Docker Compose

The production simulation stack is defined in
`infra/docker-compose.prod.yml`. It builds three application images:

- `api`: FastAPI app, migrations run at container startup, served by Uvicorn.
- `analytics-worker`: Kafka click-event consumer.
- `web`: Vite static assets served by nginx. nginx also proxies `/api` and `/r`
  to the API container so the browser can use same-origin requests locally.

Internal service communication uses Docker DNS names: `postgres`, `redis`,
`kafka`, and `api`. Persistent Postgres, Redis, and Kafka data are stored in
named Docker volumes.

Create a local production-simulation env file from the placeholder template:

```text
copy .env.example .env
```

Replace every placeholder secret before starting the stack. At minimum,
`POSTGRES_PASSWORD`, `JWT_SECRET`, and `IP_HASH_SECRET` must be strong random
values. The checked-in `.env.example` intentionally contains placeholders only;
the real `.env` file is gitignored.

Start the full stack from the repository root. Because the compose file lives in
`infra/`, pass the root `.env` explicitly for variable interpolation:

```text
docker-compose --env-file .env -f infra/docker-compose.prod.yml up --build
```

With newer Docker Compose installations, the equivalent command is:

```text
docker compose --env-file .env -f infra/docker-compose.prod.yml up --build
```

Verify health checks:

```text
docker-compose --env-file .env -f infra/docker-compose.prod.yml ps
```

Expected result: `postgres`, `redis`, `kafka`, `api`, and `web` report healthy.
The analytics worker has an image-level import health check and should stay
running after Kafka is healthy.

Smoke checks:

```text
curl http://localhost:8080/health
curl http://localhost:8080/api/health
```

Then verify the application path from the browser at `http://localhost:8080`:
register, log in, create a link, open its `/r/{short_code}` redirect, and view
the analytics page after the worker consumes click events.
