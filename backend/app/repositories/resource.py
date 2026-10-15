"""SignalFlow 后端 - 资源监控 Repository。"""

from app.models.resource import (
    ApiEndpointState,
    DatabaseState,
    ResourceAlert,
    ServerState,
    SystemLogEntry,
)
from app.repositories.base import BaseRepository


class ServerStateRepository(BaseRepository[ServerState, str]):
    """服务器状态数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, ServerState)


class DatabaseStateRepository(BaseRepository[DatabaseState, str]):
    """数据库状态数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, DatabaseState)


class ApiEndpointStateRepository(BaseRepository[ApiEndpointState, str]):
    """API 端点状态数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, ApiEndpointState)


class SystemLogEntryRepository(BaseRepository[SystemLogEntry, str]):
    """系统日志数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, SystemLogEntry)


class ResourceAlertRepository(BaseRepository[ResourceAlert, str]):
    """资源告警数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, ResourceAlert)
