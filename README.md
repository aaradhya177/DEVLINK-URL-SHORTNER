# DEVLINK

Distributed Link Intelligence Platform: a production-grade URL shortener with analytics.

The architecture source of truth is [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Local infrastructure

Start PostgreSQL, Redis, and Kafka:

```powershell
docker compose -f infra/docker-compose.yml up
```

The application services are intentionally not included in Docker Compose yet.

Default local ports:

- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Kafka external listener: `localhost:9092`

## API

```powershell
cd apps/api
poetry install
Copy-Item .env.example .env
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

## Web

```powershell
cd apps/web
npm install
Copy-Item .env.example .env
npm run dev
```

Open `http://localhost:5173`.

## Analytics worker

```powershell
cd apps/analytics-worker
poetry install
poetry run devlink-analytics-worker
```

Expected log output includes `worker started`.

## Tooling

- Python apps use Poetry, Black, Ruff, pytest, and type hints.
- The web app uses Vite, React, TypeScript strict mode, ESLint, and Prettier.
- Commit messages should follow Conventional Commits.
