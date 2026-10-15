"""SignalFlow 后端 - 商务洞察实体模型（ORM）。

BusinessLead / MarketSignal / CommonNeed 构成「客户声音 → 商机识别」链路。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BusinessLead(Base):
    """企业合作线索。"""

    __tablename__ = "business_leads"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    feedback_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    company_name: Mapped[str] = mapped_column(String(128), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(64), nullable=True)
    company_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    size_band: Mapped[str | None] = mapped_column(String(32), nullable=True)
    matched_product: Mapped[str | None] = mapped_column(String(128), nullable=True)
    match_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_score: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[int] = mapped_column(Integer, default=0)
    stage: Mapped[str] = mapped_column(String(32), default="identified")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class MarketSignal(Base):
    """市场动向信号（AI 从反馈趋势中提炼）。"""

    __tablename__ = "market_signals"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    type: Mapped[str] = mapped_column(String(32), default="opportunity")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    severity: Mapped[int] = mapped_column(Integer, default=0)
    related_industries: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class CommonNeed(Base):
    """共性需求归纳（跨客户群体的共性痛点）。"""

    __tablename__ = "common_needs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_count: Mapped[int] = mapped_column(Integer, default=0)
    customer_count: Mapped[int] = mapped_column(Integer, default=0)
    industries: Mapped[list | None] = mapped_column(JSON, nullable=True)
    product_potential: Mapped[str | None] = mapped_column(String(256), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="open")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
