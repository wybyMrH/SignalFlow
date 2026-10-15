"""SignalFlow 后端 - 商务洞察 Repository。"""

from app.models.business import BusinessLead, CommonNeed, MarketSignal
from app.repositories.base import BaseRepository


class BusinessLeadRepository(BaseRepository[BusinessLead, str]):
    """商务线索数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, BusinessLead)


class MarketSignalRepository(BaseRepository[MarketSignal, str]):
    """市场信号数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, MarketSignal)


class CommonNeedRepository(BaseRepository[CommonNeed, str]):
    """共性需求数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, CommonNeed)
