from fastapi import FastAPI

from .config import settings

app = FastAPI(title="Rep Trainer")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "llm_provider": settings.llm_provider}
