"""SignalFlow 后端 - 客户访谈实体模型（ORM）。

InterviewRecord 存储访谈基础信息；AI 提炼结论以 JSONB 嵌入，减少表连接。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InterviewRecord(Base):
    """客户访谈记录。"""

    __tablename__ = "interview_records"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_name: Mapped[str] = mapped_column(String(128), nullable=False)
    company_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contact_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    interview_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_min: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="scheduled")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_points: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # AI 提炼结论：pain_points / needs / cooperation_intent / matched_needs / lead_candidate / lead_reason
    extraction: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    linked_feedback_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    linked_lead_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    recorder: Mapped[str | None] = mapped_column(String(64), nullable=True)
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
