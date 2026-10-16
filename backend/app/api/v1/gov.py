"""SignalFlow 后端 - 政务适配接口。

提供政务总览（诉求分级 / 热点主题 / 舆情预警 / 政策告知），对齐前端 GovOverview 契约。
"""

from typing import Any

from app.core.database import get_db
from app.services.gov import GovService
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


def _service(db: Session = Depends(get_db)) -> GovService:
    return GovService(db)


def _topic_to_dict(topic: Any) -> dict[str, Any]:
    """ORM -> 前端 GovHotTopic 契约。"""
    return {
        "id": topic.id,
        "title": topic.title,
        "summary": topic.summary,
        "coverage": topic.coverage,
        "growth": topic.growth,
        "regions": topic.regions or [],
        "department": topic.department,
        "root_cause": topic.root_cause,
        "evidence": topic.evidence,
        "task_status": topic.task_status,
        "created_at": topic.created_at.isoformat() if topic.created_at else None,
    }


def _alert_to_dict(alert: Any) -> dict[str, Any]:
    """ORM -> 前端 GovAlertItem 契约。"""
    return {
        "id": alert.id,
        "level": alert.level,
        "title": alert.title,
        "summary": alert.summary,
        "trigger": alert.trigger,
        "regions": alert.regions or [],
        "evidence_count": alert.evidence_count,
        "dispatched": alert.dispatched,
        "dispatched_to": alert.dispatched_to,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
    }


def _notice_to_dict(notice: Any) -> dict[str, Any]:
    """ORM -> 前端 GovPolicyNotice 契约。"""
    return {
        "id": notice.id,
        "title": notice.title,
        "content": notice.content,
        "status": notice.status,
        "scope": notice.scope,
        "channel": notice.channel,
        "updated_at": notice.updated_at.isoformat() if notice.updated_at else None,
    }


@router.get("/overview")
def get_gov_overview(service=Depends(_service)) -> dict:
    """政务适配总览。"""
    topics = service.list_hot_topics()
    alerts = service.list_alerts()
    notices = service.list_notices(status="published")
    return {
        "hot_topics": [_topic_to_dict(t) for t in topics[:5]],
        "alerts": [_alert_to_dict(a) for a in alerts[:5]],
        "notices": [_notice_to_dict(n) for n in notices[:5]],
        "topic_count": len(topics),
        "alert_count": len(alerts),
        "notice_count": len(notices),
    }
