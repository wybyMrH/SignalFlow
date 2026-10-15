"""SignalFlow 后端 - 审计日志模型。

记录所有关键写操作（创建、更新、删除、审批、工作流触发等），
用于安全审计、数据追溯与合规报告。

设计原则：
1. 轻量写入：审计日志表独立，避免阻塞主业务事务。
2. 异步投递：生产环境建议通过 Celery / 消息队列异步写入；骨架阶段直接写入。
3. 保留期限：按合规要求定期归档（后续切片通过定时任务实现）。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    """审计日志 ORM 模型。"""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_created_at", "created_at"),
        Index("ix_audit_logs_user_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # 操作信息
    action: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="操作类型：CREATE / UPDATE / DELETE / APPROVE / REJECT / TRIGGER / LOGIN / LOGOUT 等",
    )
    entity_type: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="被操作实体类型：Feedback / Insight / Workflow / Interview / BusinessLead 等",
    )
    entity_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="被操作实体主键",
    )

    # 操作人
    user_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="执行者用户标识（系统操作留空）",
    )

    # 详情
    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="JSON 序列化的变更详情或上下文",
    )

    # 网络信息
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="IPv4/IPv6",
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id!r}, action={self.action!r}, "
            f"entity={self.entity_type}:{self.entity_id})>"
        )
