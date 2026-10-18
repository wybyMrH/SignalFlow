"""SignalFlow 后端 - 反馈实体模型（ORM）。

定义客户反馈的权威存储结构。骨架阶段先建核心字段，
渠道适配、聚类标签、评估分数等字段在后续切片经 Alembic 迁移扩展。
"""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
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
    # 业务编号：演示/展示用短编号（如 F1048），与前端 mock 的 id 口径一致。
    # 主键仍为 uuid，编号仅用于列表/详情的可读展示，可为空（运行时新建反馈可留空）。
    code: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True, comment="业务编号（展示用，如 F1048）"
    )
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, default="default")
    source: Mapped[str] = mapped_column(String(64), index=True, default="manual")
    source_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="new", index=True)
    # pgvector 向量字段：Embedding 相似度去重与主题聚类预留（维度 1536，可配置）
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536),
        nullable=True,
        comment="反馈内容向量表示（用于相似度去重与聚类）",
    )
    # 阶段 6 前端契约扩展字段（展示/过滤用途，可空）
    sentiment: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        comment="情感倾向：positive / neutral / negative",
    )
    priority: Mapped[int] = mapped_column(
        default=0,
        comment="优先级 0-5（AI 分析切片回填）",
    )
    topic_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        comment="归属洞察主题 id",
    )
    topic_title: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        comment="归属洞察主题标题（冗余展示）",
    )
    reviewer: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="当前处理人",
    )
    reply_content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="已回复内容（人工/AI 生成）",
    )
    replied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="回复时间",
    )
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