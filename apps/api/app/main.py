from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
import uvicorn

from app.core.config import settings
from src.analytics.router import router as analytics_router
from src.auth.router import router as auth_router
from src.links.router import router as links_router
from src.redirect.router import router as redirect_router
from src.shared.correlation import correlation_id_middleware
from src.shared.logging_utils import configure_logging
from src.workspaces.router import router as workspaces_router

configure_logging(settings.log_level)

app = FastAPI(
    title="DEVLINK API",
    version="0.1.0",
    description="API service for the Distributed Link Intelligence Platform.",
)

if settings.cors_allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )


app.middleware("http")(correlation_id_middleware)


@app.middleware("http")
async def security_headers(request: Request, call_next) -> Response:
    """Attach baseline browser security headers to every API response."""
    response: Response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
    )
    if settings.app_env.lower() in {"prod", "production"}:
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )
    return response


app.include_router(auth_router)
app.include_router(links_router)
app.include_router(analytics_router)
app.include_router(redirect_router)
app.include_router(workspaces_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok"}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    """Expose Prometheus metrics without route-templating middleware."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def run() -> None:
    """Run the API server for local development."""
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()
