"""SignalFlow 后端 - 资源监控服务。

服务器 / 数据库 / API 端点健康状态、告警规则评估与系统日志查询。
阈值可通过构造参数覆盖，默认规则见 DEFAULT_ALERT_RULES。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import ValidationError
from app.core.pagination import PageParams, PageResponse
from app.models.resource import (
    ApiEndpointState,
    DatabaseState,
    ResourceAlert,
    ServerState,
    SystemLogEntry,
)
from app.repositories.resource import (
    ApiEndpointStateRepository,
    DatabaseStateRepository,
    ResourceAlertRepository,
    ServerStateRepository,
    SystemLogEntryRepository,
)
from app.services.base import ServiceBase
from sqlalchemy.orm import Session

# 默认告警阈值（可被构造参数覆盖）
DEFAULT_ALERT_RULES: dict[str, float] = {
    "cpu_threshold": 90.0,
    "mem_threshold": 90.0,
    "disk_threshold": 90.0,
    "error_rate_threshold": 0.05,
    "response_ms_threshold": 1000,
}


class ResourceService(ServiceBase):
    """资源健康与告警服务。"""

    def __init__(
        self,
        session: Session,
        *,
        server_repo: ServerStateRepository | None = None,
        db_repo: DatabaseStateRepository | None = None,
        endpoint_repo: ApiEndpointStateRepository | None = None,
        log_repo: SystemLogEntryRepository | None = None,
        alert_repo: ResourceAlertRepository | None = None,
        thresholds: dict[str, float] | None = None,
    ) -> None:
        super().__init__(session)
        self._servers = server_repo or ServerStateRepository(session)
        self._dbs = db_repo or DatabaseStateRepository(session)
        self._endpoints = endpoint_repo or ApiEndpointStateRepository(session)
        self._logs = log_repo or SystemLogEntryRepository(session)
        self._alerts = alert_repo or ResourceAlertRepository(session)
        self._thresholds = {**DEFAULT_ALERT_RULES, **(thresholds or {})}

    # ──────────────────────────────────────────────
    # 健康检查
    # ──────────────────────────────────────────────

    def overall_health(self) -> dict[str, Any]:
        """聚合各资源健康状态：healthy / warning / error 计数与整体结论。"""
        servers = self._servers.list_all()  # type: ignore[arg-type]
        dbs = self._dbs.list_all()  # type: ignore[arg-type]
        endpoints = self._endpoints.list_all()  # type: ignore[arg-type]
        resources: list[dict[str, str]] = [
            {"kind": "server", "name": s.name, "status": s.status} for s in servers
        ]
        resources += [{"kind": "database", "name": d.name, "status": d.status} for d in dbs]
        resources += [
            {"kind": "endpoint", "name": f"{e.method} {e.path}", "status": e.status}
            for e in endpoints
        ]

        error = sum(1 for r in resources if r["status"] == "error")
        healthy = sum(1 for r in resources if r["status"] == "healthy")
        if error:
            overall = "error"
        elif resources and healthy == len(resources):
            overall = "healthy"
        else:
            overall = "unknown"
        return {
            "overall": overall,
            "healthy": healthy,
            "warning": sum(1 for r in resources if r["status"] == "warning"),
            "error": error,
            "total": len(resources),
            "resources": resources,
        }

    # ──────────────────────────────────────────────
    # 告警规则评估
    # ──────────────────────────────────────────────

    def evaluate_alerts(self) -> list[ResourceAlert]:
        """按阈值评估服务器 / 数据库 / API 状态，生成新的告警记录。

        规则：
        - 任一资源 status=error → error 级告警；
        - CPU / MEM / DISK 超阈值 → warning 级告警；
        - API 错误率或响应耗时超阈值 → warning 级告警；
        - 数据库连接数 ≥ 上限 90% → warning 级告警。
        """
        created: list[ResourceAlert] = []
        for server in self._servers.list_all():  # type: ignore[arg-type]
            if server.status == "error":
                created.append(
                    self._new_alert("error", f"服务器 {server.name} 异常", target=server.name)
                )
                continue
            parts: list[str] = []
            if server.cpu >= self._thresholds["cpu_threshold"]:
                parts.append(f"CPU {server.cpu:.0f}%")
            if server.mem >= self._thresholds["mem_threshold"]:
                parts.append(f"内存 {server.mem:.0f}%")
            if server.disk >= self._thresholds["disk_threshold"]:
                parts.append(f"磁盘 {server.disk:.0f}%")
            if parts:
                created.append(
                    self._new_alert(
                        "warning",
                        f"服务器 {server.name} 负载偏高：{'，'.join(parts)}",
                        target=server.name,
                    )
                )
        for db in self._dbs.list_all():  # type: ignore[arg-type]
            if db.status == "error":
                created.append(self._new_alert("error", f"数据库 {db.name} 异常", target=db.name))
            elif db.max_connections and db.connections >= db.max_connections * 0.9:
                created.append(
                    self._new_alert(
                        "warning",
                        f"数据库 {db.name} 连接数接近上限（{db.connections}/{db.max_connections}）",
                        target=db.name,
                    )
                )
        for endpoint in self._endpoints.list_all():  # type: ignore[arg-type]
            name = f"{endpoint.method} {endpoint.path}"
            if endpoint.status == "error":
                created.append(self._new_alert("error", f"API {name} 异常", target=endpoint.path))
            elif (
                endpoint.error_rate >= self._thresholds["error_rate_threshold"]
                or endpoint.response_ms >= self._thresholds["response_ms_threshold"]
            ):
                created.append(
                    self._new_alert(
                        "warning",
                        f"API {name} 性能下降（错误率 {endpoint.error_rate:.0%} / 耗时 {endpoint.response_ms}ms）",
                        target=endpoint.path,
                    )
                )
        if created:
            self._commit()
        return created

    def _new_alert(self, level: str, title: str, *, target: str | None = None) -> ResourceAlert:
        """创建并落库一条告警（不提交事务，由 evaluate_alerts 统一提交）。"""
        alert = ResourceAlert(
            id=str(uuid.uuid4()),
            level=level,
            title=title,
            time=datetime.now(timezone.utc),
            target=target,
        )
        self._alerts.create(alert)
        return alert

    def list_alerts(self, *, level: str | None = None, limit: int = 50) -> list[ResourceAlert]:
        """按级别过滤并按时间倒序返回告警列表。"""
        alerts = sorted(
            self._alerts.list_all(),  # type: ignore[arg-type]
            key=lambda a: a.time,
            reverse=True,
        )
        if level:
            alerts = [a for a in alerts if a.level == level]
        return alerts[:limit]

    # ──────────────────────────────────────────────
    # 日志
    # ──────────────────────────────────────────────

    def add_log(
        self,
        *,
        level: str = "info",
        module: str | None = None,
        message: str,
    ) -> SystemLogEntry:
        """写入一条系统日志。"""
        if not message:
            raise ValidationError(detail="日志 message 不能为空")
        entry = SystemLogEntry(
            id=str(uuid.uuid4()),
            time=datetime.now(timezone.utc),
            level=level,
            module=module,
            message=message,
        )
        self._logs.create(entry)
        self._commit()
        return entry

    def query_logs(
        self,
        *,
        level: str | None = None,
        module: str | None = None,
        keyword: str | None = None,
        params: PageParams | None = None,
    ) -> PageResponse[SystemLogEntry]:
        """按级别 / 模块 / 关键词过滤日志并分页（内存过滤，日志量可控）。"""
        items = sorted(
            self._logs.list_all(),  # type: ignore[arg-type]
            key=lambda entry: entry.time,
            reverse=True,
        )
        if level:
            items = [e for e in items if e.level == level]
        if module:
            items = [e for e in items if e.module == module]
        if keyword:
            kw = keyword.lower()
            items = [e for e in items if kw in (e.message or "").lower()]
        if params is None:
            params = PageParams()
        total = len(items)
        start = params.offset
        end = start + params.page_size
        page_items = items[start:end]
        pages = (total + params.page_size - 1) // params.page_size if total else 0
        return PageResponse(
            items=page_items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
        )