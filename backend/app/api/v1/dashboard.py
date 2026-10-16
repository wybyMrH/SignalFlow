"""SignalFlow 后端 - 驾驶舱指标接口。

映射 DashboardService.kpi_overview() 到前端 DashboardMetrics 契约；
骨架阶段趋势/渠道占比等聚合窗口字段暂无数据来源，按契约返回默认空值。
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
    kpi = service.kpi_overview()
    return {
        "total_feedbacks": kpi["total"],
        "deduped_topics": len(kpi["top_topics"]),
        "pending": kpi["pending"],
        "resolved_today": 0,
        "high_priority": 0,
        "avg_resolve_hours": 0.0,
        # 骨架阶段标记为 mock 展示；服务层接入真实聚合后改为 false
        "mock_mode": True,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "trend": [],
        "channels": [],
    }