"""SignalFlow 后端 - Agent / Skill 接口。

三个目录契约（无 Router 前缀，路径全区声明）：
- GET /agents         预置 Agent 列表（AgentStatus）
- GET /agents/tools   Agent 可配置工具目录（AgentToolDef）
- GET /skills/catalog Skill 目录（SkillDef）
- PUT /agents/{id}/scenario  更新 Agent 角色提示词
"""

from typing import Any

from app.core.database import get_db
from app.services.agents import AgentService
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()


def _service(db: Session = Depends(get_db)) -> AgentService:
    return AgentService(db)


def _agent_to_dict(agent: Any) -> dict[str, Any]:
    """Agent ORM -> 前端 AgentStatus 契约。"""
    return {
        "id": agent.id,
        "name": agent.name,
        "category": agent.category,
        "scenario": agent.scenario,
        "enabled": agent.enabled,
        "tools": agent.tools or [],
        "bound_workflow_ids": agent.bound_workflow_ids or [],
        "run_count": agent.run_count or 0,
        "reliability": agent.reliability or 0,
        "last_run_at": agent.last_run_at.isoformat() if agent.last_run_at else None,
        "preset": agent.preset,
    }


@router.get("/agents")
def list_agents(service=Depends(_service)) -> list[dict]:
    """预置 Agent 列表。"""
    return [_agent_to_dict(agent) for agent in service.list()]


@router.get("/agents/tools")
def list_agent_tools(service=Depends(_service)) -> list[dict]:
    """Agent 可配置工具目录。"""
    return [
        {
            "key": tool.key,
            "name": tool.name,
            "category": tool.category,
            "description": tool.description,
        }
        for tool in service.list_tools()
    ]


@router.get("/skills/catalog")
def list_skill_catalog(service=Depends(_service)) -> list[dict]:
    """Skill 目录（Agent 可加载能力包）。"""
    return [
        {
            "id": skill.id,
            "name": skill.name,
            "category": skill.category,
            "description": skill.description,
            "enabled": skill.enabled,
            "owner_agent_ids": skill.owner_agent_ids or [],
        }
        for skill in service.list_skills()
    ]


class ScenarioUpdate(BaseModel):
    scenario: str


@router.put("/agents/{agent_id}/scenario")
def update_agent_scenario(
    agent_id: str,
    payload: ScenarioUpdate,
    service=Depends(_service),
) -> dict:
    """更新 Agent 角色提示词（scenario）。"""
    agent = service.get(agent_id)
    agent.scenario = payload.scenario
    service._commit()
    return {
        "code": "SUCCESS",
        "message": "Agent 提示词已更新",
        "data": _agent_to_dict(agent),
    }
