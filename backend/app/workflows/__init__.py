"""SignalFlow 后端 - LangGraph AI 工作流层。

使用 LangGraph StateGraph 编排客户反馈分析闭环：
去重 → 聚类 → 影响评估 → 优先级 → 决策/回复草稿。

节点均为纯函数（``FeedbackAnalysisState -> FeedbackAnalysisState``），
支持 LLM 网关注入与离线规则模式（``workflow_llm_enabled=False``）；
状态可通过 PostgreSQL Checkpoint 持久化以支持中断恢复。
"""

from app.workflows.checkpoint import get_checkpointer, setup_checkpoint
from app.workflows.graph import analysis_graph, build_analysis_graph
from app.workflows.nodes import (
    cluster_node,
    dedup_node,
    draft_node,
    eval_node,
    priority_node,
)
from app.workflows.state import FeedbackAnalysisState

__all__ = [
    "FeedbackAnalysisState",
    "analysis_graph",
    "build_analysis_graph",
    "cluster_node",
    "dedup_node",
    "draft_node",
    "eval_node",
    "get_checkpointer",
    "priority_node",
    "setup_checkpoint",
]