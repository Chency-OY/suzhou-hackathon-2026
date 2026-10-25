from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def mount_frontend(app: FastAPI, dist: Path) -> bool:
    """若 dist/index.html 存在，则托管静态资源并为非 /api 路径做 SPA 回退。必须在所有 API 路由注册之后调用。"""
    dist = Path(dist).resolve()
    index = dist / "index.html"
    if not index.exists():
        return False
    if (dist / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "接口不存在"}})
        target = (dist / full_path).resolve()
        if full_path and dist in target.parents and target.is_file():
            return FileResponse(target)
        return FileResponse(index)

    return True
