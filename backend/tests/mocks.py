"""SignalFlow 后端 - Service 单元测试公共 mock。

Repository / Session 以内存对象替代，Service 层可脱离数据库独立验证业务规则。
契约对齐 BaseRepository 与 SQLAlchemy Session 的常用方法。
"""

from __future__ import annotations

from typing import Any

from app.core.exceptions import NotFoundError


class FakeSession:
    """SQLAlchemy Session 的极简 mock：记录事务操作与 add 的对象。"""

    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0
        self.flushes = 0
        self.joined: list[Any] = []

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def flush(self) -> None:
        self.flushes += 1

    def add(self, obj: Any) -> None:
        self.joined.append(obj)

    def refresh(self, _obj: Any) -> None:  # pragma: no cover - mock 无需真实刷新
        pass


class MemoryRepo:
    """通用内存 Repository：模拟 list_all / get_by_id / create / add 契约。"""

    def __init__(self, items: list[Any] | None = None) -> None:
        self._items = list(items or [])

    def list_all(self) -> list[Any]:
        return list(self._items)

    def get_by_id(self, obj_id: Any) -> Any | None:
        for item in self._items:
            if str(getattr(item, "id", "")) == str(obj_id):
                return item
        return None

    def get_by_id_or_404(self, obj_id: Any) -> Any:
        item = self.get_by_id(obj_id)
        if item is None:
            raise NotFoundError(resource="资源")
        return item

    def create(self, obj: Any) -> Any:
        self._items.append(obj)
        return obj

    def add(self, *args: Any, **kwargs: Any) -> Any:
        """兜底 add：按原样保存（需要 Data→ORM 转换的仓储在子类重写）。"""
        obj = args[0] if args else kwargs.get("data")
        return self.create(obj)