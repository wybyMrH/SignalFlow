"""SignalFlow 后端 - 可复用 Repository 基类。

设计原则：
1. 泛型设计：BaseRepository[T, IDType] 适配任意 ORM 模型与主键类型。
2. 职责内聚：只负责 CRUD 与基础查询，不涉业务规则（业务规则在 Service 层）。
3. 分页友好：所有 list 方法支持可选 PageParams，返回 PageResponse。
4. 审计钩子：提供创建/更新时的审计字段注入点（created_at / updated_at）。
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.pagination import PageParams, PageResponse, paginate

ModelT = TypeVar("ModelT", bound=Base)
IDT = TypeVar("IDT")


class BaseRepository(Generic[ModelT, IDT]):
    """泛型 Repository 基类。

    用法示例：
        class FeedbackRepository(BaseRepository[Feedback, int]):
            def __init__(self, db: Session):
                super().__init__(db, Feedback)
    """

    def __init__(self, db: Session, model: type[ModelT]) -> None:
        self._db = db
        self._model = model

    # ------------------------------------------------------------------
    # 基础 CRUD
    # ------------------------------------------------------------------

    def get_by_id(self, obj_id: IDT) -> ModelT | None:
        """按主键查找单条记录。"""
        return self._db.get(self._model, obj_id)

    def get_by_id_or_404(self, obj_id: IDT) -> ModelT:
        """按主键查找，不存在时抛出 NotFoundError（需在 Service 层或异常处理器中处理）。"""
        obj = self.get_by_id(obj_id)
        if obj is None:
            from app.core.exceptions import NotFoundError
            raise NotFoundError(resource=self._model.__name__)
        return obj

    def list_all(
        self,
        *,
        params: PageParams | None = None,
        order_by: Any | None = None,
    ) -> PageResponse[ModelT] | list[ModelT]:
        """返回全部记录，或分页结果。

        Args:
            params: 如果提供则返回分页结果；否则返回全部（谨慎使用，避免大数据量）。
            order_by: SQLAlchemy order_by 表达式，如 `desc(Model.created_at)`。
        """
        stmt = select(self._model)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        if params is None:
            return list(self._db.scalars(stmt).all())
        return paginate(self._db.execute(stmt), params)

    def create(self, obj: ModelT) -> ModelT:
        """插入新记录并 flush（获取自增主键），不 commit（事务由调用方控制）。"""
        self._db.add(obj)
        self._db.flush()
        self._db.refresh(obj)
        return obj

    def update(self, obj: ModelT, **kwargs: Any) -> ModelT:
        """部分更新对象字段，自动刷新。"""
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        self._db.flush()
        self._db.refresh(obj)
        return obj

    def delete(self, obj: ModelT) -> None:
        """删除记录（物理删除）。如需软删除，请在 Service 层覆写为更新 is_deleted 字段。"""
        self._db.delete(obj)
        self._db.flush()

    def count(self) -> int:
        """返回表总记录数。"""
        from sqlalchemy import func
        return self._db.scalar(select(func.count()).select_from(self._model)) or 0

    # ------------------------------------------------------------------
    # 批量操作（可选，大数据量场景）
    # ------------------------------------------------------------------

    def bulk_create(self, objs: list[ModelT]) -> list[ModelT]:
        """批量插入，效率高于逐条 create。"""
        self._db.add_all(objs)
        self._db.flush()
        for obj in objs:
            self._db.refresh(obj)
        return objs

    def bulk_delete(self, ids: list[IDT]) -> int:
        """按主键批量删除，返回删除数量。"""
        stmt = select(self._model).where(self._model.id.in_(ids))  # type: ignore[attr-defined]
        objs = self._db.scalars(stmt).all()
        for obj in objs:
            self._db.delete(obj)
        self._db.flush()
        return len(objs)
