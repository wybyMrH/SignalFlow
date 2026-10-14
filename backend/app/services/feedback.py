"""SignalFlow 后端 - 反馈服务。

骨架阶段：提供创建反馈的授权入口，并预留接入 LangGraph 工作流的钩子。
后续切片在此注入去重/聚类/痛点归纳/回复草稿等 AI 编排。
"""

import uuid

from sqlalchemy.orm import Session

from app.models.feedback import Feedback
from app.repositories.feedback import FeedbackRepository
from app.schemas.feedback import FeedbackCreate


class FeedbackService:
    """反馈相关业务服务。"""

    def __init__(self, session: Session) -> None:
        self._repo = FeedbackRepository(session)

    def create(self, data: FeedbackCreate, tenant_id: str = "default") -> Feedback:
        """新增反馈并落库。

        骨架阶段直接写入；后续切片可选择在此触发 LangGraph 异步分析工作流
        （去重 → 聚类 → 痛点归纳 → 影响评估），通过消息队列解耦。
        """
        return self._repo.add(data, tenant_id=tenant_id)

    def get(self, feedback_id: uuid.UUID) -> Feedback | None:
        """按 id 读取反馈（供状态查询与后续洞察回填）。"""
        return self._repo.get(feedback_id)