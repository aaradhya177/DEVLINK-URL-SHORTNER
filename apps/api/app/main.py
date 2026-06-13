from fastapi import FastAPI
import uvicorn

from src.auth.router import router as auth_router
from src.links.router import router as links_router
from src.workspaces.router import router as workspaces_router

app = FastAPI(
    title="DEVLINK API",
    version="0.1.0",
    description="API service for the Distributed Link Intelligence Platform.",
)

app.include_router(auth_router)
app.include_router(links_router)
app.include_router(workspaces_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok"}


def run() -> None:
    """Run the API server for local development."""
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()
