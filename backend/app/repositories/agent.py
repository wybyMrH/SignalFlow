"""SignalFlow 后端 - Agent 与 Skill Repository。"""

from app.models.agent import Agent, AgentTool, Skill
from app.repositories.base import BaseRepository


class AgentRepository(BaseRepository[Agent, str]):
    """Agent 数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, Agent)


class AgentToolRepository(BaseRepository[AgentTool, str]):
    """Agent 工具数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, AgentTool)


class SkillRepository(BaseRepository[Skill, str]):
    """Skill 数据访问层。"""

    def __init__(self, db) -> None:
        super().__init__(db, Skill)
