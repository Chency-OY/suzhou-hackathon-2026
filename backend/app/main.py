from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.auth import router as auth_router
from .api.diary import router as diary_router
from .api.playbook import router as playbook_router
from .api.products import router as products_router
from .api.radar import router as radar_router
from .api.scenarios import router as scenarios_router
from .api.sessions import router as sessions_router
from .api.team import router as team_router
from .config import settings
from .static import mount_frontend

app = FastAPI(title="Rep Trainer")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(scenarios_router)
app.include_router(sessions_router)
app.include_router(auth_router)
app.include_router(diary_router)
app.include_router(radar_router)
app.include_router(team_router)
app.include_router(playbook_router)
app.include_router(products_router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "llm_provider": settings.llm_provider}


# SPA 静态托管必须在所有 API 路由（含 health）注册之后，否则兜底路由会吞掉 /api/*
mount_frontend(app, settings.frontend_dist)
