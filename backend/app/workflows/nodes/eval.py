"""影响评估节点（EvalNode）。

输入：themes + pain_points
输出：impact_assessments（影响面数值 + 客户价值评分）

LLM 启用时：调用评估提示词；
禁用时：基于 pain_points 规则计算 impact_score / customer_value / confidence。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.logging import get_logger
from app.workflows.state import FeedbackAnalysisState

if TYPE_CHECKING:
    from app.llm.gateway import LLMGateway

logger = get_logger(__name__)


def eval_node(
    state: FeedbackAnalysisState,
    *,
    gateway: "LLMGateway | None" = None,
) -> FeedbackAnalysisState:
    """评估节点：计算影响面与客户价值。"""
    pain_points: list[dict] = state.get("pain_points", [])
    if not pain_points:
        return {**state, "impact_assessments": []}

    if gateway is None or not gateway.enabled:
        logger.info("EvalNode: LLM disabled, rule-based scoring")
        assessments = []
        for pp in pain_points:
            severity = pp.get("severity", 3)
            evidence = pp.get("evidence_count", 1)
            impact_score = min(100, severity * 10 + evidence * 5)
            customer_value = min(100, 40 + evidence * 8)
            confidence = min(1.0, 0.5 + evidence * 0.05)
            assessments.append({
                "topic": pp.get("topic", ""),
                "impact_score": impact_score,
                "customer_value": customer_value,
                "confidence": round(confidence, 2),
            })
        return {**state, "impact_assessments": assessments}

    try:
        from app.llm.prompts import load
        topics_text = "\n".join(
            f"- {pp.get('topic', '')} (severity={pp.get('severity', 3)}, evidence={pp.get('evidence_count', 1)})"
            for pp in pain_points
        )
        messages = load("eval", topics=topics_text)
        result = gateway.complete_structured(messages, workflow="eval")
        raw = result.get("assessments", [])
        assessments = []
        for item in raw:
            assessments.append({
                "topic": item.get("topic", ""),
                "impact_score": min(100, item.get("impact_score", 0)),
                "customer_value": min(100, item.get("customer_value", 0)),
                "confidence": min(1.0, item.get("confidence", 0.0)),
            })
        return {**state, "impact_assessments": assessments}
    except Exception:
        logger.exception("EvalNode LLM failed; fallback to rule-based")
        return eval_node(state, gateway=None)
