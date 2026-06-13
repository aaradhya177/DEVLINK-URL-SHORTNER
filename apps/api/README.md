# DEVLINK API

FastAPI service for link CRUD, redirects, auth, and event publishing.

## Run locally

```powershell
poetry install
Copy-Item .env.example .env
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://localhost:8000/health
```
