"""SignalFlow 后端 - 客户访谈 Repository。"""

from app.models.interview import InterviewRecord
from app.repositories.base import BaseRepository


class InterviewRecordRepository(BaseRepository[InterviewRecord, str]):
    """客户访谈记录数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, InterviewRecord)
