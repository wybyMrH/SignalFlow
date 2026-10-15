"""SignalFlow 后端 - AI 自动化实体模型（ORM）。

包含自动分类结果、去重合并组、优先级规则与调整记录。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AutomationRule(Base):
    """AI 自动化规则配置（如自动分类、去重、优先级）。"""

    __tablename__ = "automation_rules"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    scenario: Mapped[str | None] = mapped_column(String(64), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tone: Mapped[str | None] = mapped_column(String(16), nullable=True)
    stats: Mapped[str | None] = mapped_column(String(64), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ClassificationResult(Base):
    """单条反馈的自动分类结果。"""

    __tablename__ = "classification_results"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    feedback_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    suggested_topic: Mapped[str] = mapped_column(String(256), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    alternatives: Mapped[list | None] = mapped_column(JSON, nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)


class DedupGroup(Base):
    """去重合并组。"""

    __tablename__ = "dedup_groups"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    representative_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    members: Mapped[list | None] = mapped_column(JSON, nullable=True)
    merged_topic: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    merged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    repeat_count: Mapped[int] = mapped_column(Integer, default=1)


class PriorityRule(Base):
    """优先级评分规则（RICE 等模型维度配置）。"""

    __tablename__ = "priority_rules"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    factors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    threshold: Mapped[float] = mapped_column(Float, default=0.0)
    auto_escalate: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class PriorityAdjustment(Base):
    """优先级调整记录。"""

    __tablename__ = "priority_adjustments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    feedback_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    old_priority: Mapped[int] = mapped_column(Integer, default=0)
    new_priority: Mapped[int] = mapped_column(Integer, default=0)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    triggered_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    adjusted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
