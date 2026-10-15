"""SignalFlow 后端 - 资源监控实体模型（ORM）。

服务器、数据库、API 端点状态与系统日志、告警的持久化结构。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ServerState(Base):
    """服务器节点状态。"""

    __tablename__ = "server_states"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cpu: Mapped[float] = mapped_column(Float, default=0.0)
    mem: Mapped[float] = mapped_column(Float, default=0.0)
    disk: Mapped[float] = mapped_column(Float, default=0.0)
    load: Mapped[str | None] = mapped_column(String(32), nullable=True)
    uptime: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="healthy")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class DatabaseState(Base):
    """数据库实例状态。"""

    __tablename__ = "database_states"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    engine: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="healthy")
    connections: Mapped[int] = mapped_column(Integer, default=0)
    max_connections: Mapped[int] = mapped_column(Integer, default=0)
    slow_queries: Mapped[int] = mapped_column(Integer, default=0)
    tablespace_pct: Mapped[float] = mapped_column(Float, default=0.0)
    last_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ApiEndpointState(Base):
    """API 端点状态。"""

    __tablename__ = "api_endpoint_states"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    method: Mapped[str] = mapped_column(String(8), nullable=False)
    path: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="healthy")
    response_ms: Mapped[int] = mapped_column(Integer, default=0)
    error_rate: Mapped[float] = mapped_column(Float, default=0.0)
    rps: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SystemLogEntry(Base):
    """系统日志条目。"""

    __tablename__ = "system_log_entries"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    level: Mapped[str] = mapped_column(String(16), default="info")
    module: Mapped[str | None] = mapped_column(String(64), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)


class ResourceAlert(Base):
    """资源告警。"""

    __tablename__ = "resource_alerts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    level: Mapped[str] = mapped_column(String(16), default="info")
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    target: Mapped[str | None] = mapped_column(String(128), nullable=True)
