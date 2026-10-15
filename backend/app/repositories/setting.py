"""SignalFlow 后端 - 系统设置 Repository。"""

from app.models.setting import ChannelConfig, Setting
from app.repositories.base import BaseRepository


class SettingRepository(BaseRepository[Setting, str]):
    """系统设置数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, Setting)


class ChannelConfigRepository(BaseRepository[ChannelConfig, str]):
    """渠道配置数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, ChannelConfig)
