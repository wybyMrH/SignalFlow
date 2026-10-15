"""SignalFlow 后端 - 分析工作流图构建。

工作流编排客户反馈分析闭环：
START → dedup → cluster → eval → priority → draft → END

每个节点接收可选的 ``LLMGateway``（经闭包注入）；当
``workflow_llm_enabled=False`` 或网关不可用时，节点自动退化为
规则/mock 实现，保证全链路可离线运行与测试。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, TypeVar

from langgraph.graph import END, START, StateGraph

from app.core.config import settings
from app.core.logging import get_logger
from app.workflows.nodes import cluster_node, dedup_node, draft_node, eval_node, priority_node
from app.workflows.state import FeedbackAnalysisState

if TYPE_CHECKING:
    from app.llm.gateway import LLMGateway

logger = get_logger(__name__)

T = TypeVar("T")


def _with_gateway(
    node: Callable[..., FeedbackAnalysisState],
    gateway: "LLMGateway | None",
) -> Callable[[FeedbackAnalysisState], FeedbackAnalysisState]:
    """把可选网关绑定到节点闭包，保持节点签名的可测试性。"""

    def _run(state: FeedbackAnalysisState) -> FeedbackAnalysisState:
        return node(state, gateway=gateway)

    return _run


def build_analysis_graph(
    *,
    gateway: "LLMGateway | None" = None,
) -> StateGraph:
    """组装 LangGraph 分析工作流图（未编译）。

    参数：
        gateway: 可选的 LLM 网关；为 None 时节点走规则/mock 路径。
    返回：
        可继续配置或直接 ``compile()`` 的 :class:`StateGraph`。
    """
    builder = StateGraph(FeedbackAnalysisState)

    builder.add_node("dedup", _with_gateway(dedup_node, gateway))
    builder.add_node("cluster", _with_gateway(cluster_node, gateway))
    builder.add_node("eval", _with_gateway(eval_node, gateway))
    builder.add_node("priority", _with_gateway(priority_node, gateway))
    builder.add_node("draft", _with_gateway(draft_node, gateway))

    builder.add_edge(START, "dedup")
    builder.add_edge("dedup", "cluster")
    builder.add_edge("cluster", "eval")
    builder.add_edge("eval", "priority")
    builder.add_edge("priority", "draft")
    builder.add_edge("draft", END)

    return builder


# 模块级预热：使用默认网关（未注入时为 None，节点走规则路径）。
analysis_graph = build_analysis_graph(gateway=None).compile()

logger.info(
    "Analysis graph ready: workflow_llm_enabled=%s (%s)",
    settings.workflow_llm_enabled,
    "LLM 已注入" if settings.workflow_llm_enabled else "规则/mock 模式",
)