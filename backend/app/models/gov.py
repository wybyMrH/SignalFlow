"""SignalFlow 后端 - 政务适配实体模型（ORM）。

政务模块包含热点主题、舆情预警、政策告知与审计留痕。
GovOverview 为聚合视图，不单独建表；其余实体持久化。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class GovHotTopic(Base):
    """政务热点主题聚类。"""

    __tablename__ = "gov_hot_topics"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    coverage: Mapped[int] = mapped_column(Integer, default=0)
    growth: Mapped[float] = mapped_column(Float, default=0.0)
    regions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_status: Mapped[str] = mapped_column(String(32), default="pending")
    task_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class GovAlertItem(Base):
    """舆情与风险预警。"""

    __tablename__ = "gov_alert_items"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    level: Mapped[str] = mapped_column(String(16), default="blue")
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger: Mapped[str | None] = mapped_column(String(256), nullable=True)
    regions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    dispatched: Mapped[bool] = mapped_column(Boolean, default=False)
    dispatched_to: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class GovPolicyNotice(Base):
    """政策告知。"""

    __tablename__ = "gov_policy_notices"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    scope: Mapped[str | None] = mapped_column(String(128), nullable=True)
    channel: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    read_rate: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
