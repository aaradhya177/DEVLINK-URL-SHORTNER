# Security Hardening Checklist

This checklist follows the OWASP API Security Top 10 themes for the current
DEVLINK implementation.

## Input Validation

Status: **Fixed**

- Pydantic request models now reject unexpected fields with `extra="forbid"`.
- URL, alias, password, and bulk-size length limits are enforced.
- Redirect destinations must be `http` or `https`.
- Redirect destinations reject localhost names, `*.localhost`, loopback,
  private, link-local, multicast, reserved, and unspecified IP literals unless
  `ALLOW_PRIVATE_REDIRECT_URLS=true`.

Rationale: inline DNS resolution is not performed during request validation to
avoid redirect latency and DNS rebinding ambiguity. Production deployments should
keep `ALLOW_PRIVATE_REDIRECT_URLS=false` and may add async DNS/IP reputation
checks later if needed.

## Security Headers

Status: **Fixed**

FastAPI now adds:

- `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none'`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Strict-Transport-Security` when `APP_ENV=production`

## CORS

Status: **Fixed**

CORS is disabled unless `CORS_ALLOWED_ORIGINS` is configured. When enabled, it
uses explicit origins, credentials, limited methods, and limited request headers.
Wildcard origins are not used.

## Secrets Handling

Status: **Verified**

- No private keys or cloud credential patterns were found by grep.
- `.env.example` uses local endpoints and placeholders; production secrets are
  documented in `docs/DEPLOYMENT.md`.
- `JWT_SECRET` rejects known placeholder values and requires at least 32
  characters.

## Password-Protected Links

Status: **Fixed**

- Redirect password verification is rate-limited per short code and hashed
  client identifier.
- Password hashes use Passlib bcrypt verification rather than plaintext
  comparison.
- Successful verification issues a short-lived redirect token and httpOnly
  cookie.

## JWT And Refresh Tokens

Status: **Verified**

- JWT decoding explicitly allows only configured HS algorithms; `none` is not
  accepted.
- Tokens require `exp`, `iat`, `sub`, and `type`.
- Access tokens are short-lived by default.
- Refresh tokens are stored hashed, rotated on use, and old refresh tokens are
  revoked so reuse is blocked.

## Dependency Vulnerability Scanning

Status: **Fixed / Verified**

- `npm audit --audit-level=high` initially found a high-severity Vite/esbuild
  advisory. Vite and `@vitejs/plugin-react` were upgraded; the audit now reports
  zero vulnerabilities.
- A full `pip-audit` of the shared Python environment found unrelated vulnerable
  packages that are not DEVLINK dependencies. Project-path auditing is blocked
  because the Poetry files do not expose PEP 621 `[project]` metadata.
- Project-relevant pinned direct dependency audits were run with
  `pip-audit -r ... --no-deps` for the API and analytics worker and reported no
  known vulnerabilities after upgrading `PyJWT`, `FastAPI`, `Starlette`, and
  `Pillow` declarations.

Deferred: introduce committed Poetry lock files or exported hashed requirements
in Phase 13 so CI can audit full transitive dependency graphs without relying on
the shared developer environment.

## SQL Injection Review

Status: **Verified**

- API CRUD and analytics queries use SQLAlchemy ORM/select constructs.
- Raw SQL in the analytics worker and maintenance scripts uses SQLAlchemy
  `text(...)` with bound parameters.
- No string-concatenated SQL patterns were found by grep.
- Alembic DDL contains one generated partition name based on server-side date
  code, not user input.

## Remaining Deferred Security Work

- Add lock-file based Python dependency audits in CI.
- Add host allow/block lists for branded domains if product requirements need
  stricter redirect target governance.
- Add deployment-level TLS, proxy, and trusted-host configuration in Phase 13.
