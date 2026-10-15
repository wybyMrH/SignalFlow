"""SignalFlow 后端 - 工作流节点实现。

每个节点均为纯函数：``FeedbackAnalysisState -> FeedbackAnalysisState``，
支持 LLM 网关注入与离线 mock 模式（``workflow_llm_enabled=False``）。
"""

from app.workflows.nodes.cluster import cluster_node
from app.workflows.nodes.dedup import dedup_node
from app.workflows.nodes.draft import draft_node
from app.workflows.nodes.eval import eval_node
from app.workflows.nodes.priority import priority_node

__all__ = ["dedup_node", "cluster_node", "eval_node", "priority_node", "draft_node"]
