"""SignalFlow 后端 - 反馈服务。

反馈生命周期管理：
    new → analyzing → ai_reviewing → ai_replied → replied → closed
      └─────────────→ resolved ───────────────────┘
服务层封装状态机校验、批量操作与列表查询；AI 分析工作流在阶段 3
通过 llm/gateway.py 抽象接口异步接入，本层不直接调用 LLM。
"""

from __future__ import annotations

import uuid
from typing import Any

from app.core.exceptions import ValidationError
from app.core.pagination import PageParams, PageResponse
from app.models.feedback import Feedback
from app.repositories.feedback import FeedbackRepository
from app.schemas.feedback import FeedbackCreate
from app.services.base import ServiceBase
from sqlalchemy.orm import Session

# 合法的状态迁移表（key: 当前状态 → value: 可迁移到的状态集合）
FEEDBACK_STATUS_FLOW: dict[str, set[str]] = {
    "new": {"analyzing", "ai_reviewing", "resolved", "closed"},
    "analyzing": {"ai_reviewing", "new", "resolved"},
    "ai_reviewing": {"ai_replied", "resolved", "new"},
    "ai_replied": {"replied", "resolved", "closed"},
    "replied": {"resolved", "closed"},
    "resolved": {"closed"},
    "closed": set(),
}

# 待处理状态（用于驾驶舱 KPI）
PENDING_STATUSES = {"new", "analyzing", "ai_reviewing"}


class FeedbackService(ServiceBase):
    """反馈业务服务：生命周期、批量操作与列表查询。"""

    def __init__(
        self,
        session: Session,
        *,
        repo: FeedbackRepository | None = None,
    ) -> None:
        super().__init__(session)
        self._repo = repo or FeedbackRepository(session)

    # ──────────────────────────────────────────────
    # 创建与查询
    # ──────────────────────────────────────────────

    def create(self, data: FeedbackCreate, tenant_id: str = "default") -> Feedback:
        """新增反馈并落库，初始状态为 new。"""
        feedback = self._repo.add(data, tenant_id=tenant_id)
        self._commit()
        return feedback

    def get(self, feedback_id: uuid.UUID) -> Feedback | None:
        """按主键读取反馈。"""
        return self._repo.get_by_id(feedback_id)

    def list(
        self,
        *,
        source: str | None = None,
        status: str | None = None,
        keyword: str | None = None,
        params: PageParams | None = None,
    ) -> PageResponse[Feedback]:
        """按来源/状态/关键词过滤反馈列表并分页。

        现阶段的过滤在内存中进行（反馈量级可控）；
        数据量增长后可将条件下推到 Repository 的 SQL 查询。
        """
        items: list[Feedback] = list(self._repo.list_all())  # type: ignore[arg-type]
        if source:
            items = [it for it in items if it.source == source]
        if status:
            items = [it for it in items if it.status == status]
        if keyword:
            kw = keyword.lower()
            items = [
                it
                for it in items
                if kw in (it.content or "").lower() or kw in (it.author or "").lower()
            ]
        if params is None:
            params = PageParams()

        # 排序：创建时间倒序（与前端 mock listFeedbacks 口径一致，保证两端列表同序）。
        # 两趟稳定排序：先按业务编号升序（等价于 mock 数组的入库顺序），
        # 再按创建时间倒序，使相同时间戳的记录顺序也与 mock 一致。
        items = sorted(items, key=lambda it: getattr(it, "code", None) or str(it.id))
        items = sorted(items, key=lambda it: it.created_at, reverse=True)

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

    # ──────────────────────────────────────────────
    # 状态流转
    # ──────────────────────────────────────────────

    def change_status(self, feedback_id: uuid.UUID, new_status: str) -> Feedback:
        """按状态机校验并流转反馈状态，非法迁移抛出 ValidationError。"""
        feedback = self._repo.get_by_id_or_404(feedback_id)
        allowed = FEEDBACK_STATUS_FLOW.get(feedback.status, set())
        if new_status not in allowed:
            raise ValidationError(
                detail=f"非法状态流转：{feedback.status} → {new_status}",
                errors=[
                    {
                        "field": "status",
                        "message": f"{feedback.status} 只能流转到 {sorted(allowed)}",
                    }
                ],
            )
        feedback.status = new_status
        self._commit()
        return feedback

    def batch_change_status(self, feedback_ids: list[uuid.UUID], new_status: str) -> int:
        """批量流转状态，逐条校验；任一非法即整体回滚。"""
        try:
            changed = 0
            for fid in feedback_ids:
                self.change_status_raw(fid, new_status)
                changed += 1
            self._commit()
            return changed
        except Exception:
            self._rollback()
            raise

    def change_status_raw(self, feedback_id: uuid.UUID, new_status: str) -> Feedback:
        """不提交事务的状态流转（供批量操作共享事务边界）。"""
        feedback = self._repo.get_by_id_or_404(feedback_id)
        allowed = FEEDBACK_STATUS_FLOW.get(feedback.status, set())
        if new_status not in allowed:
            raise ValidationError(
                detail=f"非法状态流转：{feedback.status} → {new_status}",
                errors=[
                    {
                        "field": "status",
                        "message": f"{feedback.status} 只能流转到 {sorted(allowed)}",
                    }
                ],
            )
        feedback.status = new_status
        return feedback

    # ──────────────────────────────────────────────
    # 统计
    # ──────────────────────────────────────────────

    def count_by_status(self) -> dict[str, int]:
        """按状态统计反馈数量。"""
        result: dict[str, int] = {}
        for it in self._repo.list_all():  # type: ignore[arg-type]
            result[it.status] = result.get(it.status, 0) + 1
        return result

    def pending_count(self) -> int:
        """待处理反馈数（new/analyzing/ai_reviewing）。"""
        return sum(
            count for status, count in self.count_by_status().items() if status in PENDING_STATUSES
        )

    def high_priority_count(self, threshold: int = 4) -> int:
        """高优先级反馈数（priority >= threshold，与前端 mock 口径一致）。"""
        return sum(
            1 for it in self._repo.list_all() if (getattr(it, "priority", 0) or 0) >= threshold
        )