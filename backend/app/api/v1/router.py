"""SignalFlow 后端 - API v1 路由聚合。"""

from app.api.v1 import feedback, health, insights
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(feedback.router, prefix="/feedbacks", tags=["feedbacks"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])