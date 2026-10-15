"""SignalFlow 后端 - 政务适配服务。

诉求分级分类、督办（热点主题任务）规则引擎、舆情预警计算。
舆情预警依赖洞察服务（InsightService）的优先级打分，本层不直接调用 LLM。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import NotFoundError, ValidationError
from app.models.gov import GovAlertItem, GovHotTopic, GovPolicyNotice
from app.repositories.gov import (
    GovAlertItemRepository,
    GovHotTopicRepository,
    GovPolicyNoticeRepository,
)
from app.services.base import ServiceBase
from app.services.insight import InsightService
from sqlalchemy.orm import Session

# 诉求分级关键词表（red > orange > yellow > blue，命中即取最高级别）
GOV_LEVEL_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("red", ("死亡", "事故", "爆炸", "群体", "中毒")),
    ("orange", ("投诉", "曝光", "舆情", "维权", "媒体")),
    ("yellow", ("排队", "等待", "叫号", "材料", "窗口", "预约")),
]

# 舆情预警阈值：洞察主题优先级 ≥ 该值生成预警
GOV_ALERT_PRIORITY_THRESHOLD = 60

# 督办状态机
TOPIC_TASK_FLOW: dict[str, set[str]] = {
    "pending": {"processing", "done"},
    "processing": {"done"},
    "done": set(),
}


class GovService(ServiceBase):
    """政务诉求与舆情服务。"""

    def __init__(
        self,
        session: Session,
        *,
        topic_repo: GovHotTopicRepository | None = None,
        alert_repo: GovAlertItemRepository | None = None,
        notice_repo: GovPolicyNoticeRepository | None = None,
        insight_service: InsightService | None = None,
    ) -> None:
        super().__init__(session)
        self._topics = topic_repo or GovHotTopicRepository(session)
        self._alerts = alert_repo or GovAlertItemRepository(session)
        self._notices = notice_repo or GovPolicyNoticeRepository(session)
        self._insights = insight_service or InsightService(session)

    # ──────────────────────────────────────────────
    # 诉求分级分类（纯函数）
    # ──────────────────────────────────────────────

    @staticmethod
    def classify_complaint(content: str | None) -> str:
        """按关键词为诉求文本分级（red/orange/yellow/blue）。

        规则：从上到下逐级匹配，命中最高级别即为结果；默认 blue。
        """
        text = (content or "").lower()
        for level, keywords in GOV_LEVEL_KEYWORDS:
            if any(kw.lower() in text for kw in keywords):
                return level
        return "blue"

    # ──────────────────────────────────────────────
    # 热点主题（督办对象）
    # ──────────────────────────────────────────────

    def create_hot_topic(
        self,
        title: str,
        *,
        summary: str | None = None,
        coverage: int = 0,
        growth: float = 0.0,
        regions: list[str] | None = None,
        department: str | None = None,
        root_cause: str | None = None,
        evidence: str | None = None,
    ) -> GovHotTopic:
        """创建热点主题，初始状态为待督办（pending）。"""
        if not title:
            raise ValidationError(detail="热点主题标题不能为空")
        topic = GovHotTopic(
            id=str(uuid.uuid4()),
            title=title,
            summary=summary,
            coverage=coverage,
            growth=growth,
            regions=regions or [],
            department=department,
            root_cause=root_cause,
            evidence=evidence,
            task_status="pending",
            created_at=datetime.now(timezone.utc),
        )
        self._topics.create(topic)
        self._commit()
        return topic

    def list_hot_topics(self, *, status: str | None = None) -> list[GovHotTopic]:
        """返回全部热点主题（按创建时间倒序），可按督办状态过滤。"""
        topics = sorted(
            self._topics.list_all(),  # type: ignore[arg-type]
            key=lambda t: t.created_at,
            reverse=True,
        )
        if status:
            topics = [t for t in topics if t.task_status == status]
        return topics

    def update_topic_status(self, topic_id: str, new_status: str) -> GovHotTopic:
        """按督办状态机流转热点主题（pending → processing → done）。"""
        topic = self._topics.get_by_id(topic_id)
        if topic is None:
            raise NotFoundError(resource="政务热点主题")
        allowed = TOPIC_TASK_FLOW.get(topic.task_status, set())
        if new_status not in allowed:
            raise ValidationError(
                detail=f"非法督办状态流转：{topic.task_status} → {new_status}",
                errors=[
                    {
                        "field": "task_status",
                        "message": f"{topic.task_status} 只能流转到 {sorted(allowed)}",
                    }
                ],
            )
        topic.task_status = new_status
        self._commit()
        return topic

    # ──────────────────────────────────────────────
    # 舆情预警
    # ──────────────────────────────────────────────

    def create_alert(
        self,
        *,
        level: str,
        title: str,
        summary: str | None = None,
        trigger: str | None = None,
        regions: list[str] | None = None,
        evidence_count: int = 0,
        dispatched: bool = False,
        dispatched_to: str | None = None,
    ) -> GovAlertItem:
        """创建一条舆情 / 风险预警。"""
        if level not in {"red", "orange", "yellow", "blue"}:
            raise ValidationError(detail=f"非法预警级别：{level}")
        if not title:
            raise ValidationError(detail="预警标题不能为空")
        alert = GovAlertItem(
            id=str(uuid.uuid4()),
            level=level,
            title=title,
            summary=summary,
            trigger=trigger,
            regions=regions or [],
            evidence_count=evidence_count,
            dispatched=dispatched,
            dispatched_to=dispatched_to,
            created_at=datetime.now(timezone.utc),
        )
        self._alerts.create(alert)
        self._commit()
        return alert

    def evaluate_insight_alerts(self) -> list[GovAlertItem]:
        """基于洞察主题优先级生成舆情预警（依赖洞察服务）。

        规则：priority_score >= GOV_ALERT_PRIORITY_THRESHOLD 且尚未生成同标题
        预警时，创建一条 orange 级预警。
        """
        created: list[GovAlertItem] = []
        existing_titles = {a.title for a in self._alerts.list_all()}  # type: ignore[arg-type]
        for topic in self._insights.list():
            if topic.priority_score < GOV_ALERT_PRIORITY_THRESHOLD:
                continue
            if topic.title in existing_titles:
                continue
            alert = GovAlertItem(
                id=str(uuid.uuid4()),
                level="orange",
                title=topic.title,
                summary=(
                    f"高频诉求主题，优先级 {topic.priority_score}"
                    f"（信号强度 {topic.strength}）"
                ),
                trigger="insight_priority",
                regions=[],
                evidence_count=topic.feedback_count or 0,
                dispatched=False,
                created_at=datetime.now(timezone.utc),
            )
            self._alerts.create(alert)
            created.append(alert)
        if created:
            self._commit()
        return created

    def dispatch_alert(self, alert_id: str, *, to: str) -> GovAlertItem:
        """派发预警到指定部门并标记为已派发。"""
        alert = self._alerts.get_by_id(alert_id)
        if alert is None:
            raise NotFoundError(resource="政务预警")
        if not to:
            raise ValidationError(detail="派发对象不能为空")
        alert.dispatched = True
        alert.dispatched_to = to
        self._commit()
        return alert

    def list_alerts(
        self,
        *,
        level: str | None = None,
        dispatched: bool | None = None,
    ) -> list[GovAlertItem]:
        """返回预警列表（按创建时间倒序），可按级别 / 派发状态过滤。"""
        alerts = sorted(
            self._alerts.list_all(),  # type: ignore[arg-type]
            key=lambda a: a.created_at,
            reverse=True,
        )
        if level:
            alerts = [a for a in alerts if a.level == level]
        if dispatched is not None:
            alerts = [a for a in alerts if a.dispatched == dispatched]
        return alerts

    # ──────────────────────────────────────────────
    # 政策告知
    # ──────────────────────────────────────────────

    def create_notice(
        self,
        title: str,
        content: str,
        *,
        scope: str | None = None,
        channel: str | None = None,
        status: str = "draft",
    ) -> GovPolicyNotice:
        """创建政策告知（默认草稿状态）。"""
        if not title or not content:
            raise ValidationError(detail="政策告知标题与内容不能为空")
        notice = GovPolicyNotice(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            status=status,
            scope=scope,
            channel=channel,
            updated_at=datetime.now(timezone.utc),
        )
        self._notices.create(notice)
        self._commit()
        return notice

    def publish_notice(self, notice_id: str) -> GovPolicyNotice:
        """发布政策告知（draft → published）。"""
        notice = self._notices.get_by_id(notice_id)
        if notice is None:
            raise NotFoundError(resource="政策告知")
        notice.status = "published"
        notice.updated_at = datetime.now(timezone.utc)
        self._commit()
        return notice

    def list_notices(self, *, status: str | None = None) -> list[GovPolicyNotice]:
        """返回政策告知列表，可按状态过滤。"""
        notices = list(self._notices.list_all())  # type: ignore[arg-type]
        if status:
            notices = [n for n in notices if n.status == status]
        return notices