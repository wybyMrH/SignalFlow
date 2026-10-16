"""SignalFlow 后端 - 资源监控接口。

提供资源健康总览、告警与日志查询，对齐前端 ResourceDetail / ResourceHealth 契约。
"""

from typing import Any

from app.core.database import get_db
from app.services.resources import ResourceService
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


def _service(db: Session = Depends(get_db)) -> ResourceService:
    return ResourceService(db)


def _alert_to_dict(alert: Any) -> dict[str, Any]:
    """ORM -> 前端告警契约。"""
    return {
        "id": alert.id,
        "level": alert.level,
        "title": alert.title,
        "time": alert.time.isoformat() if alert.time else None,
        "target": alert.target,
    }


@router.get("/overview")
def get_resource_overview(service=Depends(_service)) -> dict:
    """资源管理总览（服务器 / 数据库 / API / 日志 / 告警）。"""
    health = service.overall_health()
    alerts = service.list_alerts(limit=10)
    return {
        "health": health,
        "alerts": [_alert_to_dict(a) for a in alerts],
        "updated_at": health.get("updated_at"),
    }


@router.get("/health")
def get_resource_health(service=Depends(_service)) -> dict:
    """资源健康概况（总览驾驶舱展示用）。"""
    return service.overall_health()
