"""SignalFlow 后端 - 反馈仓储。

继承 BaseRepository 提供标准 CRUD，同时保留业务友好的 add/get 快捷方法。
后续切片扩展去重查询（语义相似）、分页列表、状态流转等方法。
"""

import uuid

from sqlalchemy.orm import Session

from app.models.feedback import Feedback
from app.repositories.base import BaseRepository
from app.schemas.feedback import FeedbackCreate


class FeedbackRepository(BaseRepository[Feedback, uuid.UUID]):
    """基于 SQLAlchemy Session 的反馈仓储。"""

    def __init__(self, session: Session) -> None:
        super().__init__(session, Feedback)

    def add(self, data: FeedbackCreate, tenant_id: str = "default") -> Feedback:
        """新增一条反馈并立即提交（幂等调用方负责去重）。"""
        feedback = Feedback(
            tenant_id=tenant_id,
            source=data.source,
            source_ref=data.source_ref,
            content=data.content,
            author=data.author,
            status="new",
        )
        return self.create(feedback)

    def get(self, feedback_id: uuid.UUID) -> Feedback | None:
        """按主键查询反馈。"""
        return self.get_by_id(feedback_id)

    def get_by_source_ref(
        self, source_ref: str, *, tenant_id: str = "default"
    ) -> Feedback | None:
        """按渠道幂等键查询已入库反馈（用于入站处理器去重）。"""
        return (
            self._db.query(Feedback)
            .filter(
                Feedback.source_ref == source_ref,
                Feedback.tenant_id == tenant_id,
            )
            .first()
        )