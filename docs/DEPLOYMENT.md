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
