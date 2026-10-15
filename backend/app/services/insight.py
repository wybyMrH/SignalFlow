"""SignalFlow 后端 - 洞察主题服务。

负责「反馈 → 洞察」聚合：将一批同主题反馈聚合成 InsightTopic，
计算信号强度与优先级评分卡，并维护证据链（可追溯到原始反馈）。
本服务是 LangGraph ClusterNode/EvaluateNode 的输出落库边界，
AI 细节（Embedding/聚类）不进入本层，仅接收已分组的反馈输入。
"""

from __future__ import annotations

import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable

from app.core.exceptions import NotFoundError, ValidationError
from app.models.feedback import Feedback
from app.models.insight import InsightTopic
from app.repositories.insight import InsightTopicRepository
from app.services.base import ServiceBase
from sqlalchemy.orm import Session

# 强度计算权重（可配置化前的默认值）
STRENGTH_PER_FEEDBACK = 20
STRENGTH_PER_CUSTOMER = 5
STRENGTH_MAX = 100
PRIORITY_MAX = 100

# 情感 → 优先级加成（负面反馈更紧急）
SENTIMENT_PRIORITY_BONUS: dict[str, int] = {"negative": 15, "neutral": 5, "positive": 0}


class InsightService(ServiceBase):
    """洞察主题聚合与评分服务。"""

    def __init__(
        self,
        session: Session,
        *,
        repo: InsightTopicRepository | None = None,
    ) -> None:
        super().__init__(session)
        self._repo = repo or InsightTopicRepository(session)

    # ──────────────────────────────────────────────
    # 聚合计算（纯函数，便于单元测试）
    # ──────────────────────────────────────────────

    def compute_strength(self, feedback_count: int, customer_count: int) -> int:
        """信号强度 = 反馈量 × 权重 + 客户数 × 权重，封顶 100。"""
        value = (
            feedback_count * STRENGTH_PER_FEEDBACK + customer_count * STRENGTH_PER_CUSTOMER
        )
        return max(0, min(STRENGTH_MAX, value))

    def compute_priority_score(
        self,
        *,
        feedback_count: int,
        customer_count: int,
        sentiment: str = "neutral",
    ) -> int:
        """优先级总分 = 信号强度 + 情感加成，封顶 100。"""
        strength = self.compute_strength(feedback_count, customer_count)
        bonus = SENTIMENT_PRIORITY_BONUS.get(sentiment, 0)
        return max(0, min(PRIORITY_MAX, strength + bonus))

    @staticmethod
    def compute_trend(current: int, previous: int | None) -> str:
        """趋势判断：较上一周期增长为 up、下降为 down、持平为 flat。"""
        if previous is None or previous == 0:
            return "flat" if current == 0 else "up"
        if current > previous:
            return "up"
        if current < previous:
            return "down"
        return "flat"

    # ──────────────────────────────────────────────
    # 聚合落库
    # ──────────────────────────────────────────────

    def aggregate_feedback(
        self,
        title: str,
        feedbacks: Iterable[Feedback],
        *,
        short: str | None = None,
        sentiment: str = "neutral",
    ) -> InsightTopic:
        """将一组同主题反馈聚合成（或更新）洞察主题。

        - feedback_count：组内反馈总数
        - customer_count：去重后的客户（author）数
        - evidence：逐条反馈的证据链
        - strength / priority_score：由评分规则计算
        """
        feedback_list = list(feedbacks)
        if not feedback_list:
            raise ValidationError(detail="聚合反馈集不能为空")

        customers = {f.author or "匿名" for f in feedback_list}
        feedback_count = len(feedback_list)
        customer_count = len(customers)
        strength = self.compute_strength(feedback_count, customer_count)
        bonus = SENTIMENT_PRIORITY_BONUS.get(sentiment, 0)
        priority = self.compute_priority_score(
            feedback_count=feedback_count,
            customer_count=customer_count,
            sentiment=sentiment,
        )

        evidence = [
            {
                "feedback_id": str(f.id),
                "excerpt": (f.content[:120] + "…") if len(f.content) > 120 else f.content,
                "author": f.author,
                "source": f.source,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "sentiment": sentiment,
            }
            for f in feedback_list
        ]

        topic = self.find_by_title(title)
        if topic is None:
            topic = InsightTopic(
                id=str(uuid.uuid4()),
                title=title,
                short=short,
                feedback_count=feedback_count,
                customer_count=customer_count,
                trend="up" if feedback_count > 0 else "flat",
                strength=strength,
                priority_score=priority,
                score_card={
                    "total": priority,
                    "max": PRIORITY_MAX,
                    "level": self._level_of(priority),
                    "dimensions": [
                        {
                            "key": "strength",
                            "label": "信号强度",
                            "score": strength,
                            "max": STRENGTH_MAX,
                            "note": f"{feedback_count} 条反馈 / {customer_count} 家客户",
                        },
                        {
                            "key": "sentiment",
                            "label": "情感加成",
                            "score": bonus,
                            "max": SENTIMENT_PRIORITY_BONUS.get("negative", 0),
                            "note": f"情感倾向：{sentiment}",
                        },
                    ],
                },
                evidence=evidence,
                last_seen_at=datetime.now(timezone.utc),
            )
            self._repo.create(topic)
        else:
            topic.feedback_count = feedback_count
            topic.customer_count = customer_count
            topic.strength = strength
            topic.priority_score = priority
            topic.evidence = evidence
            topic.last_seen_at = datetime.now(timezone.utc)
            self._db.flush()
            self._db.refresh(topic)
        self._commit()
        return topic

    @staticmethod
    def _level_of(score: int) -> str:
        """得分 → 优先级等级（critical/high/medium/low）。"""
        if score >= 80:
            return "critical"
        if score >= 60:
            return "high"
        if score >= 40:
            return "medium"
        return "low"

    # ──────────────────────────────────────────────
    # 查询
    # ──────────────────────────────────────────────

    def find_by_title(self, title: str) -> InsightTopic | None:
        """按标题精确匹配主题（聚合更新使用）。"""
        for topic in self._repo.list_all():  # type: ignore[arg-type]
            if topic.title == title:
                return topic
        return None

    def get(self, topic_id: str) -> InsightTopic:
        """按主键读取主题，不存在时抛 NotFoundError。"""
        topic = self._repo.get_by_id(topic_id)
        if topic is None:
            raise NotFoundError(resource="洞察主题")
        return topic

    def list(self) -> list[InsightTopic]:
        """返回全部洞察主题（按优先级降序）。"""
        return sorted(
            self._repo.list_all(),  # type: ignore[arg-type]
            key=lambda t: t.priority_score,
            reverse=True,
        )

    def dashboard_stats(self) -> dict[str, Any]:
        """洞察看板统计：主题数、覆盖反馈数、去重客户数。"""
        topics = self.list()
        feedback_ids: set[str] = set()
        customers: set[str] = set()
        for topic in topics:
            for item in topic.evidence or []:
                if isinstance(item, dict) and item.get("feedback_id"):
                    feedback_ids.add(str(item["feedback_id"]))
                if isinstance(item, dict) and item.get("author"):
                    customers.add(str(item["author"]))
        return {
            "topic_count": len(topics),
            "feedback_count": len(feedback_ids),
            "customer_count": len(customers),
            "top_topics": [t.title for t in topics[:5]],
        }