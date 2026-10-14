"""SignalFlow 后端 - 分析工作流图构建。

骨架阶段的图：始终贯通所有节点，但 LLM/Embedding 节点在
`workflow_llm_enabled=False` 时走"旁路占位"实现，保证可离线运行与测试。
后续切片逐个将旁路替换为真实实现（llm 网关 + 向量检索）。
"""

from langgraph.graph import END, START, StateGraph

from app.core.config import settings
from app.core.logging import get_logger
from app.workflows.state import FeedbackAnalysisState

logger = get_logger(__name__)


def _dedup_node(state: FeedbackAnalysisState) -> FeedbackAnalysisState:
    """去重节点：骨架占位。真实实现基于 Embedding 相似度分组。"""
    ids = state.get("feedback_ids", [])
    # 骨架：无重复假设，每个 id 自成一组
    return {
        **state,
        "dedup_groups": [[i] for i in ids],
    }


def _cluster_node(state: FeedbackAnalysisState) -> FeedbackAnalysisState:
    """聚类节点：骨架占位。真实实现基于向量聚类（HDBSCAN 等）。"""
    logger.info("cluster node (skeleton): %s", state.get("feedback_ids"))
    return {
        **state,
        "clusters": [],
    }


def _insight_node(state: FeedbackAnalysisState) -> FeedbackAnalysisState:
    """痛点归纳节点：骨架占位。真实实现调用 Aware LLM 摘要。"""
    logger.info("insight node (skeleton): llm_enabled=%s", settings.workflow_llm_enabled)
    return {
        **state,
        "pain_points": [],
        "themes": [],
    }


def _assess_node(state: FeedbackAnalysisState) -> FeedbackAnalysisState:
    """影响评估节点：骨架占位。真实实现计算影响面与优先级评分。"""
    return {
        **state,
        "impact_assessments": [],
        "priorities": [],
        "decisions": [],
    }


def _draft_node(state: FeedbackAnalysisState) -> FeedbackAnalysisState:
    """回复草稿节点：骨架占位。真实实现基于决策与痛点生成客户回复草稿。"""
    return {
        **state,
        "reply_drafts": [],
    }


def build_analysis_graph():
    """组装 LangGraph 分析工作流图。返回可编译/可调用的 CompiledGraph。"""
    builder = StateGraph(FeedbackAnalysisState)

    builder.add_node("dedup", _dedup_node)
    builder.add_node("cluster", _cluster_node)
    builder.add_node("insight", _insight_node)
    builder.add_node("assess", _assess_node)
    builder.add_node("draft", _draft_node)

    builder.add_edge(START, "dedup")
    builder.add_edge("dedup", "cluster")
    builder.add_edge("cluster", "insight")
    builder.add_edge("insight", "assess")
    builder.add_edge("assess", "draft")
    builder.add_edge("draft", END)

    return builder.compile()


analysis_graph = build_analysis_graph()