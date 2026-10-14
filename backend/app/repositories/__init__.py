"""SignalFlow 后端 - 数据访问层（Repository）。

Repository 负责将 ORM 操作封装为可测试、可替换的仓储接口；
服务层只依赖 Repository，不直接操作 Session。
"""

from app.repositories.feedback import FeedbackRepository

__all__ = ["FeedbackRepository"]