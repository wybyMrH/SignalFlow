"""SignalFlow 后端 - 反馈仓储。

骨架阶段提供最小编排：插入、按 id 查询。后续切片扩展
去重查询（语义相似）、分页列表、状态流转等方法。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate


class FeedbackRepository:
    """基于 SQLAlchemy Session 的反馈仓储。"""

    def __init__(self, session: Session) -> None:
        self._session = session

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
        self._session.add(feedback)
        self._session.commit()
        self._session.refresh(feedback)
        return feedback

    def get(self, feedback_id: uuid.UUID) -> Feedback | None:
        """按主键查询反馈。"""
        stmt = select(Feedback).where(Feedback.id == feedback_id)
        return self._session.execute(stmt).scalar_one_or_none()