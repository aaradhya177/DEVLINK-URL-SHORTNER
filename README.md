# DEVLINK

[![CI](https://github.com/aaradhya177/DEVLINK-URL-SHORTNER/actions/workflows/ci.yml/badge.svg)](https://github.com/aaradhya177/DEVLINK-URL-SHORTNER/actions/workflows/ci.yml)

DEVLINK is a production-oriented URL shortener with authentication, workspaces,
low-latency redirects, Redis caching, asynchronous click analytics, malicious URL
checks, QR codes, observability, CI/CD, and deployment infrastructure.

It is built as a portfolio-grade distributed system: small enough to run locally,
but designed with the same boundaries a larger production system would need.

## Architecture

```text
                              +----------------------+
                              | apps/web             |
                              | React + TypeScript   |
                              +----------+-----------+
                                         |
                                         | JSON API / redirects
                                         v
                              +----------+-----------+
                              | apps/api             |
                              | FastAPI              |
                              | auth, links, RBAC,   |
                              | redirects, metrics   |
                              +----+----------+------+
                                   |          |
                           SQL     |          | cache, rate limits
                                   v          v
                            +------+---+  +---+------+
                            | Postgres |  | Redis    |
                            +------+---+  +----------+
                                   ^
                                   |
                              aggregates
                                   |
                            +------+-------------+
                            | apps/analytics-    |
                            | worker             |
                            | Kafka consumer     |
                            +------+-------------+
                                   ^
                                   |
                                Kafka
```

## Features

- JWT auth with refresh-token rotation and revocation.
- Workspace RBAC: owner, admin, editor, viewer.
- Link CRUD with custom aliases, expiration, password protection, soft delete,
  and deduplication by normalized URL hash.
- Public redirect endpoint at `/r/{short_code}` with Redis cache-aside lookup.
- QR code generation as PNG or SVG.
- Bulk URL shortening with per-item results.
- Async click analytics pipeline through Kafka.
- Daily analytics rollups for summary, time-series, geo, and device charts.
- URL safety checks with Google Safe Browsing provider support.
- Privacy-aware analytics: no raw IP persistence; referrers reduced to domains.
- API and worker JSON logs with correlation IDs.
- Prometheus metrics and Terraform CloudWatch alarms/dashboard.
- Dockerfiles, production-like Compose, Terraform AWS path, and GitHub Actions.

## Repository Layout

```text
apps/
  api/                FastAPI service, Alembic migrations, API tests
  analytics-worker/   Kafka consumer and analytics aggregation worker
  web/                React + TypeScript dashboard
docs/                 Architecture, API spec, deployment, monitoring, runbooks
infra/
  docker-compose.yml       local Postgres/Redis/Kafka
  docker-compose.prod.yml  production-like local stack
  terraform/              AWS ECS/RDS/Redis/ALB infrastructure
  scripts/                deployment helper scripts
```

## Local Development

Start shared infrastructure:

```powershell
docker compose -f infra/docker-compose.yml up
```

Default ports:

- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Kafka: `localhost:9092`

Run the API:

```powershell
cd apps/api
poetry install
Copy-Item .env.example .env
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run the web app:

```powershell
cd apps/web
npm install
Copy-Item .env.example .env
npm run dev
```

Open `http://localhost:5173`.

Run the analytics worker:

```powershell
cd apps/analytics-worker
poetry install
poetry run devlink-analytics-worker
```

Health and docs:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

OpenAPI UI is available from FastAPI at:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

The exported OpenAPI spec is `docs/api-spec.yaml`.

## Testing

Backend:

```powershell
cd apps/api
pytest
pytest --cov
```

Analytics worker:

```powershell
cd apps/analytics-worker
pytest
pytest --cov
```

Frontend:

```powershell
cd apps/web
npm run lint
npm test
npm run build
```

Database-backed integration tests require a migrated disposable test database:

```powershell
$env:TEST_DATABASE_URL="postgresql+asyncpg://devlink:devlink@localhost:5432/devlink_test"
```

## Production-Like Local Stack

The production-style Compose file builds and runs API, worker, web, Postgres,
Redis, and Kafka:

```powershell
Copy-Item .env.example .env
docker compose --env-file .env -f infra/docker-compose.prod.yml up --build
```

Open `http://localhost:8080`.

## Deployment

The AWS path uses Terraform and GitHub Actions:

- ECS Fargate for API, worker, web, and a low-cost Kafka-compatible broker.
- RDS PostgreSQL.
- ElastiCache Redis.
- Application Load Balancer.
- CloudWatch logs, dashboard, and alarms.
- GHCR image publishing and ECS task-definition updates on merge to `main`.

See `docs/DEPLOYMENT.md`.

Important: the AWS stack costs money if left running. Use it for demos or
production experiments, then tear it down when not needed.

## Documentation

- `docs/ARCHITECTURE.md`: current implemented architecture.
- `docs/SYSTEM_DESIGN_INTERVIEW.md`: standalone system-design walkthrough.
- `docs/api-spec.yaml`: generated OpenAPI specification.
- `docs/DEPLOYMENT.md`: Docker Compose and AWS deployment runbook.
- `docs/MONITORING.md`: logs, metrics, alarms, and runbooks.
- `docs/PERFORMANCE.md`: performance notes and local load-test plan.
- `docs/QUERY_PLANS.md`: query-plan review for hot paths.
- `docs/SECURITY.md`: security hardening checklist.
- `docs/TODO.md`: future work and deferred improvements.

## Tooling

- Python: FastAPI, SQLAlchemy async, Alembic, Pydantic, Poetry, pytest, Ruff,
  Black.
- Worker: aiokafka, SQLAlchemy async, GeoIP/user-agent parsing, Prometheus
  client.
- Frontend: React, TypeScript, Vite, React Query, Recharts, Vitest.
- Infrastructure: Docker Compose, Terraform, GitHub Actions, GHCR.
