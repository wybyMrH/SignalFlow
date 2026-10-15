"""草稿节点（DraftNode）。

输入：decisions + 原始反馈内容
输出：reply_drafts（回复草稿 / 产品任务草稿）

LLM 启用时：调用草稿生成提示词；
禁用时：返回模板化草稿。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.logging import get_logger
from app.workflows.state import FeedbackAnalysisState

if TYPE_CHECKING:
    from app.llm.gateway import LLMGateway

logger = get_logger(__name__)


def draft_node(
    state: FeedbackAnalysisState,
    *,
    gateway: "LLMGateway | None" = None,
) -> FeedbackAnalysisState:
    """草稿节点：为高优先级主题生成回复草稿。"""
    decisions: list[dict] = state.get("decisions", [])
    if not decisions:
        return {**state, "reply_drafts": []}

    if gateway is None or not gateway.enabled:
        logger.info("DraftNode: LLM disabled, template drafts")
        drafts = []
        for d in decisions:
            topic = d.get("topic", "该问题")
            drafts.append({
                "content": f"关于「{topic}」的回复草稿：感谢您的反馈，我们会尽快安排产品团队跟进，预计在下一版本迭代中优先处理。",
                "target_feedback_ids": [],
                "priority": min(100, int(d.get("confidence", 0.5) * 100)),
                "topic": topic,
            })
        return {**state, "reply_drafts": drafts}

    try:
        from app.llm.prompts import load
        decisions_text = "\n".join(
            f"- {d.get('topic', '')}: action={d.get('action', '')}, confidence={d.get('confidence', 0.0)}"
            for d in decisions
        )
        messages = load("draft", decisions=decisions_text)
        result = gateway.complete_structured(messages, workflow="draft")
        raw_drafts = result.get("drafts", [])
        drafts = []
        for rd in raw_drafts:
            drafts.append({
                "content": rd.get("content", ""),
                "target_feedback_ids": rd.get("target_feedback_ids", []),
                "priority": min(100, rd.get("priority", 50)),
                "topic": rd.get("topic", ""),
            })
        return {**state, "reply_drafts": drafts}
    except Exception:
        logger.exception("DraftNode LLM failed; fallback to template drafts")
        return draft_node(state, gateway=None)
