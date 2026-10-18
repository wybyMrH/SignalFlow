"""SignalFlow 后端 - 资源监控接口。

提供资源健康总览、告警与日志查询，对齐前端 ResourceDetail / ResourceHealth 契约。
"""

from datetime import datetime, timezone
from typing import Any

from app.core.database import get_db
from app.models.resource import ApiEndpointState, DatabaseState, ServerState, SystemLogEntry
from app.services.resources import ResourceService
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


def _service(db: Session = Depends(get_db)) -> ResourceService:
    return ResourceService(db)


def _alert_to_dict(alert: Any) -> dict[str, Any]:
    """ORM -> 前端告警契约。"""
    return {
        "id": alert.id,
        "level": alert.level,
        "title": alert.title,
        "time": alert.time.isoformat() if alert.time else None,
        "target": alert.target,
    }


def _server_to_dict(s: ServerState) -> dict[str, Any]:
    return {
        "id": s.id,
        "name": s.name,
        "role": s.role,
        "cpu": s.cpu,
        "mem": s.mem,
        "disk": s.disk,
        "load": s.load,
        "uptime": s.uptime,
        "status": s.status,
    }


def _db_to_dict(d: DatabaseState) -> dict[str, Any]:
    return {
        "id": d.id,
        "name": d.name,
        "engine": d.engine,
        "status": d.status,
        "connections": d.connections,
        "max_connections": d.max_connections,
        "slow_queries": d.slow_queries,
        "tablespace_pct": d.tablespace_pct,
        "last_check": d.last_check.isoformat() if d.last_check else None,
    }


def _endpoint_to_dict(e: ApiEndpointState) -> dict[str, Any]:
    return {
        "id": e.id,
        "method": e.method,
        "path": e.path,
        "status": e.status,
        "response_ms": e.response_ms,
        "error_rate": e.error_rate,
        "rps": e.rps,
    }


def _log_to_dict(entry: SystemLogEntry) -> dict[str, Any]:
    return {
        "id": entry.id,
        "time": entry.time.isoformat() if entry.time else None,
        "level": entry.level,
        "module": entry.module,
        "message": entry.message,
    }


@router.get("/overview")
def get_resource_overview(service=Depends(_service)) -> dict:
    """资源管理总览（服务器 / 数据库 / API / 日志 / 告警）。

    返回完整 ResourceDetail 结构，与前端 mock 契约对齐。
    """
    servers = service._servers.list_all()
    dbs = service._dbs.list_all()
    endpoints = service._endpoints.list_all()
    logs = sorted(service._logs.list_all(), key=lambda x: x.time, reverse=True)
    alerts = service.list_alerts(limit=10)

    # 取所有资源的最新更新时间
    all_times: list[datetime] = []
    for collection in [servers, dbs, endpoints, logs, alerts]:
        for item in collection:
            if hasattr(item, "updated_at") and item.updated_at:
                all_times.append(item.updated_at)
    updated_at = max(all_times).isoformat() if all_times else datetime.now(timezone.utc).isoformat()

    return {
        "servers": [_server_to_dict(s) for s in servers],
        "databases": [_db_to_dict(d) for d in dbs],
        "apis": [_endpoint_to_dict(e) for e in endpoints],
        "logs": [_log_to_dict(entry) for entry in logs],
        "alerts": [_alert_to_dict(a) for a in alerts],
        "updated_at": updated_at,
    }


@router.get("/health")
def get_resource_health(service=Depends(_service)) -> dict:
    """资源健康概况（总览驾驶舱展示用），对齐前端 ResourceHealth 契约。

    - db_status：全部 healthy -> healthy；含 error -> down；否则 degraded。
    - error_rate：全部 API 的平均错误率（百分比，保留 1 位小数）。
    - alert_count：当前告警总数。
    """
    servers = service._servers.list_all()
    dbs = service._dbs.list_all()
    endpoints = service._endpoints.list_all()
    alerts = service.list_alerts(limit=50)

    server_count = len(servers)
    server_healthy = sum(1 for s in servers if s.status == "healthy")

    db_statuses = {d.status for d in dbs}
    if any(status == "error" for status in db_statuses):
        db_status = "down"
    elif any(status != "healthy" for status in db_statuses):
        db_status = "degraded"
    else:
        db_status = "healthy"

    api_total = len(endpoints)
    api_healthy = sum(1 for e in endpoints if e.status == "healthy")
    error_rate = round(sum(e.error_rate or 0 for e in endpoints) / api_total, 1) if api_total else 0.0

    return {
        "ok": True,
        "server_count": server_count,
        "server_healthy": server_healthy,
        "db_status": db_status,
        "db_connections": sum(d.connections or 0 for d in dbs),
        "api_healthy": api_healthy,
        "api_total": api_total,
        "error_rate": error_rate,
        "alert_count": len(alerts),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
