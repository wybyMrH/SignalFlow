"""SignalFlow 后端 - 驾驶舱指标接口。

映射 DashboardService.dashboard_overview() 到前端 DashboardMetrics 契约；
趋势/渠道/今日办结等聚合字段由反馈表实时计算，与前端 mock 口径一致。
"""

from datetime import datetime, timezone

from app.core.database import get_db
from app.services.dashboard import DashboardService
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


def _service(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(db)


@router.get("/metrics")
def get_dashboard_metrics(service=Depends(_service)) -> dict:
    """总览工作台 KPI 指标。"""
    kpi = service.dashboard_overview()
    return {
        "total_feedbacks": kpi["total"],
        "deduped_topics": kpi["deduped_topics"],
        "pending": kpi["pending"],
        "resolved_today": kpi["resolved_today"],
        "high_priority": kpi["high_priority"],
        "avg_resolve_hours": kpi["avg_resolve_hours"],
        # 服务层已按反馈表实时聚合，不再是骨架 mock 占位
        "mock_mode": False,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "trend": kpi["trend"],
        "channels": kpi["channels"],
    }