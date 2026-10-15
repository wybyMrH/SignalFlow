"""SignalFlow 后端 - 工作流 Repository。"""

from app.models.workflow import Workflow, WorkflowRun
from app.repositories.base import BaseRepository


class WorkflowRepository(BaseRepository[Workflow, str]):
    """工作流定义数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, Workflow)


class WorkflowRunRepository(BaseRepository[WorkflowRun, str]):
    """工作流运行记录数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, WorkflowRun)
