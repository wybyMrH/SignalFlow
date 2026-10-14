"""SignalFlow 后端 - FastAPI 应用入口。

启动：uvicorn app.main:app --reload
"""

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="SignalFlow 客户反馈决策工具 - 后端服务",
    debug=settings.app_debug,
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict[str, str]:
    """根路径：简单服务标识。"""
    return {"service": "signalflow-backend", "docs": "/docs"}