"""SignalFlow 后端 - 工作流服务。

工作流模板管理、节点图配置校验、启用状态切换与运行记录。
Agent 绑定相关校验委托给注入的 AgentService（构造注入，避免模块级循环 import）。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from app.core.exceptions import NotFoundError, ValidationError
from app.models.workflow import Workflow, WorkflowRun
from app.repositories.workflow import WorkflowRepository, WorkflowRunRepository
from app.services.base import ServiceBase
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from app.services.agents import AgentService

# 阶段 3 将落地的 5 类 LangGraph 节点（与 workflows 层 schema 对齐）
VALID_NODE_TYPES: set[str] = {
    "ClassifyNode",
    "DedupNode",
    "ClusterNode",
    "EvaluateNode",
    "DraftNode",
}

# 工作流运行终态
WORKFLOW_RUN_FINAL_STATUSES: set[str] = {"success", "failed", "cancelled"}


class WorkflowService(ServiceBase):
    """工作流定义与执行记录服务。"""

    def __init__(
        self,
        session: Session,
        *,
        repo: WorkflowRepository | None = None,
        run_repo: WorkflowRunRepository | None = None,
        agent_service: AgentService | None = None,
    ) -> None:
        super().__init__(session)
        self._repo = repo or WorkflowRepository(session)
        self._run_repo = run_repo or WorkflowRunRepository(session)
        self._agents = agent_service

    # ──────────────────────────────────────────────
    # 节点图校验（纯函数）
    # ──────────────────────────────────────────────

    @staticmethod
    def validate_nodes(
        nodes: list[dict[str, Any]] | None,
        edges: list[dict[str, Any]] | None,
        *,
        agent_bindings: dict[str, Any] | None = None,
    ) -> list[str]:
        """校验工作流节点图配置，返回错误列表；空列表表示校验通过。

        - 节点必须含 id 且 id 唯一，type 必须属于 VALID_NODE_TYPES；
        - 边引用的 source/target 必须存在于节点集合；
        - agent_bindings 非空时，绑定的节点必须存在。
        """
        errors: list[str] = []
        node_ids: set[str] = set()
        for idx, node in enumerate(nodes or []):
            if not isinstance(node, dict) or not node.get("id"):
                errors.append(f"节点 #{idx + 1} 缺少 id")
                continue
            nid = str(node["id"])
            if nid in node_ids:
                errors.append(f"节点 id 重复：{nid}")
            node_ids.add(nid)
            ntype = node.get("type")
            if ntype not in VALID_NODE_TYPES:
                errors.append(
                    f"节点 {nid} 的 type 非法：{ntype}，仅支持 {sorted(VALID_NODE_TYPES)}"
                )
        for idx, edge in enumerate(edges or []):
            source = (edge or {}).get("source")
            target = (edge or {}).get("target")
            if source not in node_ids:
                errors.append(f"边 #{idx + 1} 引用了不存在的源节点：{source}")
            if target not in node_ids:
                errors.append(f"边 #{idx + 1} 引用了不存在的目标节点：{target}")
        for binding in (agent_bindings or {}).keys():
            if binding not in node_ids:
                errors.append(f"Agent 绑定节点不存在：{binding}")
        return errors

    # ──────────────────────────────────────────────
    # 模板管理
    # ──────────────────────────────────────────────

    def create(self, data: dict[str, Any]) -> Workflow:
        """创建工作流模板（含节点图校验）。

        data 关键字段：name / description / enabled / trigger / nodes / edges /
        agent_bindings / tool_chain。
        """
        if not data.get("name"):
            raise ValidationError(detail="工作流名称不能为空")
        errors = self.validate_nodes(
            data.get("nodes"),
            data.get("edges"),
            agent_bindings=data.get("agent_bindings"),
        )
        if errors:
            raise ValidationError(
                detail="工作流节点配置不合法",
                errors=[{"field": "nodes", "message": msg} for msg in errors],
            )
        workflow = Workflow(
            id=str(uuid.uuid4()),
            name=str(data["name"]),
            description=data.get("description"),
            enabled=bool(data.get("enabled", True)),
            trigger=data.get("trigger"),
            nodes=data.get("nodes") or [],
            edges=data.get("edges") or [],
            agent_bindings=data.get("agent_bindings"),
            tool_chain=data.get("tool_chain"),
        )
        self._repo.create(workflow)
        self._commit()
        return workflow

    def get(self, workflow_id: str) -> Workflow:
        """按主键读取工作流，不存在时抛 NotFoundError。"""
        workflow = self._repo.get_by_id(workflow_id)
        if workflow is None:
            raise NotFoundError(resource="工作流")
        return workflow

    def list(self) -> list[Workflow]:
        """返回全部工作流模板。"""
        return list(self._repo.list_all())  # type: ignore[arg-type]

    def toggle_enabled(self, workflow_id: str) -> Workflow:
        """切换工作流启用状态。"""
        workflow = self.get(workflow_id)
        workflow.enabled = not workflow.enabled
        self._commit()
        return workflow

    def update(self, workflow_id: str, data: dict[str, Any]) -> Workflow:
        """部分更新工作流；涉及节点/边变更时先重新校验。"""
        workflow = self.get(workflow_id)
        if "nodes" in data or "edges" in data:
            errors = self.validate_nodes(
                data.get("nodes", workflow.nodes),
                data.get("edges", workflow.edges),
                agent_bindings=data.get("agent_bindings", workflow.agent_bindings),
            )
            if errors:
                raise ValidationError(
                    detail="工作流节点配置不合法",
                    errors=[{"field": "nodes", "message": msg} for msg in errors],
                )
        for field in (
            "name",
            "description",
            "trigger",
            "nodes",
            "edges",
            "agent_bindings",
            "tool_chain",
        ):
            if field in data:
                setattr(workflow, field, data[field])
        if not workflow.name:
            raise ValidationError(detail="工作流名称不能为空")
        self._db.flush()
        self._commit()
        return workflow

    # ──────────────────────────────────────────────
    # 运行记录
    # ──────────────────────────────────────────────

    def start_run(self, workflow_id: str, *, trigger: str = "manual") -> WorkflowRun:
        """启动一次工作流运行（仅允许启用中的工作流）。"""
        workflow = self.get(workflow_id)
        if not workflow.enabled:
            raise ValidationError(detail="工作流已停用，无法启动运行")
        run = WorkflowRun(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            started_at=datetime.now(timezone.utc),
            status="running",
        )
        self._run_repo.create(run)
        self._commit()
        return run

    def finish_run(
        self,
        run_id: str,
        *,
        status: str,
        output_summary: str | None = None,
        error_message: str | None = None,
    ) -> WorkflowRun:
        """结束一次工作流运行并记录结果（终态：success/failed/cancelled）。"""
        if status not in WORKFLOW_RUN_FINAL_STATUSES:
            raise ValidationError(detail=f"非法运行终态：{status}")
        run = self._run_repo.get_by_id(run_id)
        if run is None:
            raise NotFoundError(resource="工作流运行记录")
        run.status = status
        run.output_summary = output_summary
        run.error_message = error_message
        run.ended_at = datetime.now(timezone.utc)
        self._commit()
        return run

    def recent_runs_grouped(
        self, *, limit: int = 30
    ) -> dict[str, list[WorkflowRun]]:
        """返回全部工作流的最近运行记录（按开始时间倒序），以 workflow_id 分组。

        用于组装前端 WorkflowDetail.history 契约（工作流配置页 / 资源管理页告警联动）。
        """
        runs = self._run_repo.list_all(order_by=WorkflowRun.started_at.desc())
        grouped: dict[str, list[WorkflowRun]] = {}
        for run in runs:
            grouped.setdefault(run.workflow_id, []).append(run)
        return {key: value[:limit] for key, value in grouped.items()}