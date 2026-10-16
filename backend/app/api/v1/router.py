"""SignalFlow 后端 - API v1 路由聚合。"""

from app.api.v1 import (
    agents,
    ai,
    dashboard,
    feedback,
    gov,
    health,
    insights,
    interviews,
    resources,
    roadmap,
    settings,
    workflows,
)
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(feedback.router, prefix="/feedbacks", tags=["feedbacks"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["interviews"])
api_router.include_router(agents.router, tags=["agents"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(resources.router, prefix="/resources", tags=["resources"])
api_router.include_router(gov.router, prefix="/gov", tags=["gov"])
api_router.include_router(roadmap.router, prefix="/roadmap", tags=["roadmap"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])