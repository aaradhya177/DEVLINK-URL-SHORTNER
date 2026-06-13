from fastapi import FastAPI
import uvicorn

from src.links.router import router as links_router

app = FastAPI(
    title="DEVLINK API",
    version="0.1.0",
    description="API service for the Distributed Link Intelligence Platform.",
)

app.include_router(links_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def run() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()
