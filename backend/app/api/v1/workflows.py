"""SignalFlow 后端 - 工作流接口。

提供工作流模板列表、目录与运行状态查询，对齐前端 WorkflowDetail / WorkflowCatalogItem 契约。
"""

from typing import Any

from app.core.database import get_db
from app.services.workflows import WorkflowService
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


def _service(db: Session = Depends(get_db)) -> WorkflowService:
    return WorkflowService(db)


def _workflow_to_dict(workflow: Any) -> dict[str, Any]:
    """ORM -> 前端 WorkflowDetail 契约。"""
    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "enabled": workflow.enabled,
        "trigger": workflow.trigger,
        "nodes": workflow.nodes or [],
        "edges": workflow.edges or [],
        "agent_bindings": workflow.agent_bindings or {},
        "tool_chain": workflow.tool_chain or {},
        "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
    }


def _run_to_dict(run: Any) -> dict[str, Any]:
    """ORM -> 前端工作流运行状态契约。"""
    return {
        "id": run.id,
        "workflow_id": run.workflow_id,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "ended_at": run.ended_at.isoformat() if run.ended_at else None,
        "output_summary": run.output_summary,
        "error_message": run.error_message,
    }


@router.get("")
def list_workflows(service=Depends(_service)) -> list[dict]:
    """工作流模板列表（含最新运行状态与运行历史）。"""
    workflows = service.list()
    runs_by_workflow = service.recent_runs_grouped()
    result = []
    for wf in workflows:
        item = _workflow_to_dict(wf)
        # 真实运行记录由 WorkflowRunRepository 查询，对齐前端 WorkflowDetail.history 契约
        item["history"] = [_run_to_dict(r) for r in runs_by_workflow.get(wf.id, [])]
        # 骨架阶段：模拟运行状态
        item["last_run"] = {
            "status": "completed" if not wf.enabled else "running",
            "progress": 100 if not wf.enabled else 67,
            "started_at": item["updated_at"],
        }
        result.append(item)
    return result


@router.get("/catalog")
def list_workflow_catalog(service=Depends(_service)) -> list[dict]:
    """工作流目录（Agent 绑定工作流用）。"""
    return [
        {
            "id": wf.id,
            "name": wf.name,
            "description": wf.description,
            "enabled": wf.enabled,
        }
        for wf in service.list()
    ]
