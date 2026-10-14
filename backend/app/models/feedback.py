"""SignalFlow 后端 - 反馈实体模型（ORM）。

定义客户反馈的权威存储结构。骨架阶段先建核心字段，
渠道适配、聚类标签、评估分数等字段在后续切片经 Alembic 迁移扩展。
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Feedback(Base):
    """一条客户反馈：保留原文与来源元数据。

    - 原文（content）为权威事实，加工字段（主题、聚类、分数）均为派生数据。
    - 渠道（source）标识反馈来源，便于渠道适配器扩展与审计。
    """

    __tablename__ = "feedbacks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, default="default")
    source: Mapped[str] = mapped_column(String(64), index=True, default="manual")
    source_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="new", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover - 仅调试用
        return f"<Feedback id={self.id} source={self.source} status={self.status}>"


# 便于后续切片使用的查询对象（按需扩展）
feedback_select = select(Feedback)