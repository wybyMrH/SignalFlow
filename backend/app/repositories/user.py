"""SignalFlow 后端 - 用户 Repository。"""

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User, str]):
    """用户数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, User)
