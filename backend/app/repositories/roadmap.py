"""SignalFlow 后端 - 路线图 Repository。"""

from app.models.roadmap import ReplyDraft, RoadmapItem, TaskItem
from app.repositories.base import BaseRepository


class RoadmapItemRepository(BaseRepository[RoadmapItem, str]):
    """路线图项目数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, RoadmapItem)


class TaskItemRepository(BaseRepository[TaskItem, str]):
    """任务数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, TaskItem)


class ReplyDraftRepository(BaseRepository[ReplyDraft, str]):
    """回复草稿数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, ReplyDraft)
