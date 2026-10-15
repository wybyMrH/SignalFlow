"""SignalFlow 后端 - Agent 服务。

Agent 启停、运行统计、工具权限校验与 Skill 管理。
工作流绑定校验委托给注入的 WorkflowService（构造注入，避免模块级循环 import）。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from app.core.exceptions import NotFoundError, ValidationError
from app.models.agent import Agent, AgentTool, Skill
from app.repositories.agent import AgentRepository, AgentToolRepository, SkillRepository
from app.services.base import ServiceBase
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from app.services.workflows import WorkflowService


class AgentService(ServiceBase):
    """AI Agent 管理服务。"""

    def __init__(
        self,
        session: Session,
        *,
        repo: AgentRepository | None = None,
        tool_repo: AgentToolRepository | None = None,
        skill_repo: SkillRepository | None = None,
        workflow_service: WorkflowService | None = None,
    ) -> None:
        super().__init__(session)
        self._repo = repo or AgentRepository(session)
        self._tool_repo = tool_repo or AgentToolRepository(session)
        self._skill_repo = skill_repo or SkillRepository(session)
        self._workflows = workflow_service

    # ──────────────────────────────────────────────
    # Agent 管理
    # ──────────────────────────────────────────────

    def list(self) -> list[Agent]:
        """返回全部 Agent。"""
        return list(self._repo.list_all())  # type: ignore[arg-type]

    def get(self, agent_id: str) -> Agent:
        """按主键读取 Agent，不存在时抛 NotFoundError。"""
        agent = self._repo.get_by_id(agent_id)
        if agent is None:
            raise NotFoundError(resource="Agent")
        return agent

    def toggle_enabled(self, agent_id: str) -> Agent:
        """切换 Agent 启用状态。"""
        agent = self.get(agent_id)
        agent.enabled = not agent.enabled
        self._commit()
        return agent

    def record_run(self, agent_id: str, *, success: bool = True) -> Agent:
        """记录一次运行并更新统计（run_count / last_run_at / reliability）。

        可靠性规则：成功 +1，失败 -2，区间 0-100。
        """
        agent = self.get(agent_id)
        agent.run_count = (agent.run_count or 0) + 1
        agent.last_run_at = datetime.now(timezone.utc)
        if success:
            agent.reliability = min(100, (agent.reliability or 0) + 1)
        else:
            agent.reliability = max(0, (agent.reliability or 0) - 2)
        self._commit()
        return agent

    @staticmethod
    def _tool_keys(tools: list[Any] | None) -> set[str]:
        """归一化工具配置为 key 集合（支持 dict 或字符串两种形态）。"""
        keys: set[str] = set()
        for item in tools or []:
            if isinstance(item, dict):
                keys.add(str(item.get("key", "")))
            else:
                keys.add(str(item))
        return {k for k in keys if k}

    def has_tool(self, agent_id: str, tool_key: str) -> bool:
        """校验 Agent 是否具备指定工具权限（未配置工具视为无权限）。"""
        agent = self.get(agent_id)
        return tool_key in self._tool_keys(agent.tools)

    def bind_workflow(self, agent_id: str, workflow_id: str) -> Agent:
        """绑定工作流到 Agent（幂等）。

        注入 WorkflowService 时先校验工作流存在，避免悬挂绑定。
        """
        agent = self.get(agent_id)
        if self._workflows is not None:
            self._workflows.get(workflow_id)
        bound = list(agent.bound_workflow_ids or [])
        if workflow_id not in bound:
            bound.append(workflow_id)
            agent.bound_workflow_ids = bound
            self._commit()
        return agent

    def summary(self) -> dict[str, Any]:
        """Agent 统计：总数 / 启用数 / 预置数 / 总运行次数。"""
        agents = self.list()
        return {
            "total": len(agents),
            "enabled": sum(1 for a in agents if a.enabled),
            "preset": sum(1 for a in agents if a.preset),
            "total_runs": sum(a.run_count or 0 for a in agents),
        }

    # ──────────────────────────────────────────────
    # 工具 / Skill 目录
    # ──────────────────────────────────────────────

    def list_tools(self) -> list[AgentTool]:
        """返回全部工具目录项。"""
        return list(self._tool_repo.list_all())  # type: ignore[arg-type]

    def list_skills(self) -> list[Skill]:
        """返回全部 Skill。"""
        return list(self._skill_repo.list_all())  # type: ignore[arg-type]

    def toggle_skill(self, skill_id: str) -> Skill:
        """切换 Skill 启用状态。"""
        skill = self._skill_repo.get_by_id(skill_id)
        if skill is None:
            raise NotFoundError(resource="Skill")
        skill.enabled = not skill.enabled
        self._commit()
        return skill