"""优先级节点（PriorityNode）。

输入：impact_assessments
输出：priorities（优先级分数 + 排序列表）+ decisions（行动建议 + 置信度）

LLM 启用时：调用 RICE 思想评分提示词；
禁用时：纯算法排序与阈值决策。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.logging import get_logger
from app.workflows.state import FeedbackAnalysisState

if TYPE_CHECKING:
    from app.llm.gateway import LLMGateway

logger = get_logger(__name__)


def priority_node(
    state: FeedbackAnalysisState,
    *,
    gateway: "LLMGateway | None" = None,
) -> FeedbackAnalysisState:
    """优先级节点：基于评估结果打分、排序并生成决策建议。"""
    assessments: list[dict] = state.get("impact_assessments", [])
    if not assessments:
        return {**state, "priorities": [], "decisions": []}

    if gateway is None or not gateway.enabled:
        logger.info("PriorityNode: LLM disabled, rule-based RICE scoring")
        priorities = []
        decisions = []
        # 按 impact_score 降序
        sorted_assessments = sorted(
            assessments, key=lambda x: x.get("impact_score", 0), reverse=True
        )
        for rank, a in enumerate(sorted_assessments, start=1):
            # 简化 RICE: impact_score * confidence / effort(默认=1)
            score = min(100, int(a.get("impact_score", 0) * a.get("confidence", 0.5)))
            priorities.append({
                "topic": a.get("topic", ""),
                "priority_score": score,
                "rank": rank,
            })
            if score >= 60:
                decisions.append({
                    "topic": a.get("topic", ""),
                    "action": "跟进",
                    "confidence": a.get("confidence", 0.5),
                })
        return {**state, "priorities": priorities, "decisions": decisions}

    try:
        from app.llm.prompts import load
        assessments_text = "\n".join(
            f"- {a.get('topic', '')}: impact={a.get('impact_score', 0)}, value={a.get('customer_value', 0)}, confidence={a.get('confidence', 0.0)}"
            for a in assessments
        )
        messages = load("priority", assessments=assessments_text)
        result = gateway.complete_structured(messages, workflow="priority")
        raw_priorities = result.get("priorities", [])
        raw_decisions = result.get("decisions", [])
        priorities = [
            {"topic": p.get("topic", ""), "priority_score": min(100, p.get("priority_score", 0)), "rank": p.get("rank", i + 1)}
            for i, p in enumerate(raw_priorities)
        ]
        decisions = [
            {"topic": d.get("topic", ""), "action": d.get("action", ""), "confidence": min(1.0, d.get("confidence", 0.0))}
            for d in raw_decisions
        ]
        return {**state, "priorities": priorities, "decisions": decisions}
    except Exception:
        logger.exception("PriorityNode LLM failed; fallback to rule-based")
        return priority_node(state, gateway=None)
