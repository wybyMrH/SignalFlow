"""SignalFlow 后端 - 洞察主题实体模型（ORM）。

InsightTopic 是 LangGraph 聚类与评估节点的产物，包含可解释的打分卡与证据链。
证据链以 JSONB 存储，保持可扩展性。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InsightTopic(Base):
    """洞察主题：聚类结果 + 评估打分卡。"""

    __tablename__ = "insight_topics"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    short: Mapped[str | None] = mapped_column(String(512), nullable=True)
    feedback_count: Mapped[int] = mapped_column(Integer, default=0)
    customer_count: Mapped[int] = mapped_column(Integer, default=0)
    trend: Mapped[str] = mapped_column(String(16), default="flat")
    strength: Mapped[int] = mapped_column(Integer, default=0)
    priority_score: Mapped[int] = mapped_column(Integer, default=0)
    # 打分卡维度存储为 JSON，便于后续扩展维度数量
    score_card: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # 证据链：列表 of {feedback_id, excerpt, author, source, created_at, sentiment}
    evidence: Mapped[list | None] = mapped_column(JSON, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
