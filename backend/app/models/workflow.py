"""SignalFlow 后端 - 工作流实体模型（ORM）。

Workflow 定义 LangGraph 风格节点图、Agent 绑定与工具链；
WorkflowRun 记录每次执行历史。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Workflow(Base):
    """工作流定义。"""

    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(default=True)
    trigger: Mapped[str | None] = mapped_column(String(32), nullable=True)
    nodes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    edges: Mapped[list | None] = mapped_column(JSON, nullable=True)
    agent_bindings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    tool_chain: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class WorkflowRun(Base):
    """工作流运行记录。"""

    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    workflow_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="running")
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
