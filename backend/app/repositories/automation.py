"""SignalFlow 后端 - AI 自动化 Repository。"""

from app.models.automation import (
    AutomationRule,
    ClassificationResult,
    DedupGroup,
    PriorityAdjustment,
    PriorityRule,
)
from app.repositories.base import BaseRepository


class AutomationRuleRepository(BaseRepository[AutomationRule, str]):
    """自动化规则数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, AutomationRule)


class ClassificationResultRepository(BaseRepository[ClassificationResult, str]):
    """分类结果数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, ClassificationResult)


class DedupGroupRepository(BaseRepository[DedupGroup, str]):
    """去重组数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, DedupGroup)


class PriorityRuleRepository(BaseRepository[PriorityRule, str]):
    """优先级规则数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, PriorityRule)


class PriorityAdjustmentRepository(BaseRepository[PriorityAdjustment, str]):
    """优先级调整数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, PriorityAdjustment)
