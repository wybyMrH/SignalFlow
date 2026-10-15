"""SignalFlow 后端 - AI 对话与工作流运行 Repository。"""

from app.models.ai_ import AIChatMessage, AIWorkflowRun
from app.repositories.base import BaseRepository


class AIChatMessageRepository(BaseRepository[AIChatMessage, str]):
    """AI 对话消息数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, AIChatMessage)


class AIWorkflowRunRepository(BaseRepository[AIWorkflowRun, str]):
    """AI 工作流运行数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, AIWorkflowRun)
