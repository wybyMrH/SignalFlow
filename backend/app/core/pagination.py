"""SignalFlow 后端 - 统一分页模型与辅助函数。

所有列表接口统一使用 PageResponse[T]，确保前端分页组件与后端响应结构一致。
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Query

T = TypeVar("T")


class PageParams(BaseModel):
    """分页请求参数。

    用法：在 router 的依赖注入中使用 `page: int = 1, page_size: int = 20`，
    然后构造 `PageParams(page=page, page_size=page_size)` 传给 service。
    """

    page: int = Field(1, ge=1, description="页码（从 1 开始）")
    page_size: int = Field(20, ge=1, le=200, description="每页条数")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PageResponse(BaseModel, Generic[T]):
    """分页响应封装。

    前端组件预期字段：items / total / page / page_size / pages。
    """

    items: list[T] = Field(default_factory=list, description="当前页数据列表")
    total: int = Field(0, description="总记录数")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页条数")
    pages: int = Field(0, description="总页数")

    @classmethod
    def empty(cls, params: PageParams) -> "PageResponse[Any]":
        """返回空分页结果（用于异常降级或零数据场景）。"""
        return cls(items=[], total=0, page=params.page, page_size=params.page_size, pages=0)


def paginate(
    query: Query[Any],
    params: PageParams,
    *,
    scalars: bool = True,
) -> PageResponse[Any]:
    """对 SQLAlchemy Query 执行分页并返回 PageResponse。

    Args:
        query: SQLAlchemy ORM Query 对象
        params: 分页参数
        scalars: 是否自动执行 .scalars().all()（默认 True）。
                 如果查询返回的是标量对象（如 ORM 实例）则为 True；
                 如果查询返回的是元组（如 join 查询）则为 False。

    Returns:
        包含总记录数与当前页数据的 PageResponse。
    """
    total: int = query.session.scalar(
        func.count().select().select_from(query.subquery())
    ) or 0

    items_query = query.offset(params.offset).limit(params.page_size)
    if scalars:
        items: list[Any] = items_query.scalars().all()
    else:
        items = items_query.all()

    pages = (total + params.page_size - 1) // params.page_size if total > 0 else 0
    return PageResponse(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=pages,
    )
