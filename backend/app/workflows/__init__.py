"""SignalFlow 后端 - LangGraph AI 工作流层。

使用 LangGraph StateGraph 编排客户反馈分析闭环：
去重 → 聚类 → 痛点归纳 → 影响评估 → 优先级 → 决策建议/回复草稿。

骨架阶段提供可运行、可测试的最小图结构与节点边界；
真实 LLM/Embedding 调用由 llm 网关按配置注入（默认关闭）。
"""

from app.workflows.graph import build_analysis_graph
from app.workflows.state import FeedbackAnalysisState

__all__ = ["FeedbackAnalysisState", "build_analysis_graph"]