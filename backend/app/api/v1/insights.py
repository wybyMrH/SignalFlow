"""SignalFlow 后端 - 洞察接口。

提供洞察看板（主题/痛点/优先级评分卡/证据链），对接 InsightService，
数据由 LangGraph 聚类与评估工作流产出后落库（InsightTopic）。
对齐前端 InsightDashboard / InsightTopic 契约。
"""

from datetime import datetime, timezone
from typing import Any

from app.core.database import get_db
from app.services.insight import InsightService
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


def _service(db: Session = Depends(get_db)) -> InsightService:
    return InsightService(db)


# 反馈来源 → 前端展示标签（TopicEvidence.source_label 契约）
_SOURCE_LABELS = {
    "ticket": "工单系统",
    "review": "应用商店评论",
    "interview": "客户访谈",
    "sales": "销售反馈",
    "hotline": "服务热线",
    "portal": "门户网站",
}


def _topic_to_dict(topic: Any) -> dict[str, Any]:
    """InsightTopic ORM -> 前端 InsightTopic 契约。"""
    evidence: list[dict[str, Any]] = []
    for item in topic.evidence or []:
        if not isinstance(item, dict):
            continue
        source = item.get("source") or ""
        evidence.append(
            {
                "feedback_id": item.get("feedback_id"),
                "excerpt": item.get("excerpt"),
                "author": item.get("author"),
                "source": source,
                "source_label": _SOURCE_LABELS.get(source, source),
                "created_at": item.get("created_at"),
                "sentiment": item.get("sentiment", "neutral"),
            }
        )
    return {
        "id": topic.id,
        "title": topic.title,
        "short": topic.short or "",
        "feedback_count": topic.feedback_count or 0,
        "customer_count": topic.customer_count or 0,
        "trend": topic.trend or "flat",
        "strength": topic.strength or 0,
        "priority_score": topic.priority_score or 0,
        "score_card": topic.score_card or {},
        "evidence": evidence,
        "last_seen_at": topic.last_seen_at.isoformat() if topic.last_seen_at else None,
        "updated_at": topic.updated_at.isoformat() if topic.updated_at else None,
    }


@router.get("")
def list_insights(service=Depends(_service)) -> dict[str, Any]:
    """洞察看板数据（主题/痛点/趋势/预警）。"""
    topics = service.list()
    return {
        "items": [_topic_to_dict(t) for t in topics],
        "total": len(topics),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }