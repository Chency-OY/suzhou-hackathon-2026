from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.scenarios import router as scenarios_router
from .config import settings

app = FastAPI(title="Rep Trainer")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(scenarios_router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "llm_provider": settings.llm_provider}
