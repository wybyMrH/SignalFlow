"""SignalFlow 后端 - FastAPI 应用入口。

启动：uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.cache import cache
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.middleware.request_log import RequestLogMiddleware

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。

    startup:  建立 Redis 缓存连接
    shutdown: 关闭 Redis 缓存连接
    """
    await cache.connect()
    yield
    await cache.disconnect()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="SignalFlow 客户反馈决策工具 - 后端服务",
    debug=settings.app_debug,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# 中间件栈（按添加顺序，请求时 outer -> inner；响应时 inner -> outer）
# 1. CORS（最外层）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 2. 请求日志与 Trace ID
app.add_middleware(RequestLogMiddleware)

# 全局异常处理器
register_exception_handlers(app)

# 路由注册
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict[str, str]:
    """根路径：简单服务标识。"""
    return {"service": "signalflow-backend", "docs": "/docs"}