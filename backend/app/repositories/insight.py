"""SignalFlow 后端 - 洞察主题 Repository。"""

from app.models.insight import InsightTopic
from app.repositories.base import BaseRepository


class InsightTopicRepository(BaseRepository[InsightTopic, str]):
    """洞察主题数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, InsightTopic)
