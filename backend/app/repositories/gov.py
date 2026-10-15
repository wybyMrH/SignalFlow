"""SignalFlow 后端 - 政务适配 Repository。"""

from app.models.gov import GovAlertItem, GovHotTopic, GovPolicyNotice
from app.repositories.base import BaseRepository


class GovHotTopicRepository(BaseRepository[GovHotTopic, str]):
    """政务热点主题数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, GovHotTopic)


class GovAlertItemRepository(BaseRepository[GovAlertItem, str]):
    """政务预警数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, GovAlertItem)


class GovPolicyNoticeRepository(BaseRepository[GovPolicyNotice, str]):
    """政策告知数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, GovPolicyNotice)
