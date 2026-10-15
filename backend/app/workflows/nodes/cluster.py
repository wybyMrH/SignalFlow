"""聚类/痛点归纳节点（ClusterNode）。

输入：dedup_groups（去重后的反馈分组）
输出：clusters（结构化聚类对象）+ themes（主题列表）+ pain_points（痛点标签）

LLM 启用时：调用 LLM JSON mode 进行主题聚类与痛点识别；
禁用时：基于简单规则生成 mock 聚类结果，保持结构一致。
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from app.core.logging import get_logger
from app.workflows.state import FeedbackAnalysisState

if TYPE_CHECKING:
    from app.llm.gateway import LLMGateway

logger = get_logger(__name__)


def cluster_node(
    state: FeedbackAnalysisState,
    *,
    gateway: "LLMGateway | None" = None,
) -> FeedbackAnalysisState:
    """聚类节点：将去重后的反馈分组提炼为主题与痛点。"""
    groups: list[list[str]] = state.get("dedup_groups", [])
    if not groups:
        return {**state, "clusters": [], "themes": [], "pain_points": []}

    if gateway is None or not gateway.enabled:
        logger.info("ClusterNode: LLM disabled, rule-based mock")
        clusters: list[dict] = []
        themes: list[str] = []
        pain_points: list[dict] = []
        for idx, member_ids in enumerate(groups):
            theme = f"主题-{idx + 1}"
            themes.append(theme)
            clusters.append({
                "id": f"cluster-{idx}",
                "member_ids": member_ids,
                "theme": theme,
                "size": len(member_ids),
            })
            pain_points.append({
                "topic": f"痛点-{idx + 1}",
                "severity": 3,
                "evidence_count": len(member_ids),
                "cluster_id": f"cluster-{idx}",
            })
        return {**state, "clusters": clusters, "themes": themes, "pain_points": pain_points}

    # LLM 模式：构造 prompt 调用 gateway.complete_structured
    try:
        from app.llm.prompts import load
        feedbacks_text = "\n".join(
            f"- Group {i}: {member_ids}" for i, member_ids in enumerate(groups)
        )
        messages = load("cluster", feedbacks=feedbacks_text)
        result = gateway.complete_structured(messages, workflow="cluster")
        raw_clusters = result.get("clusters", [])
        clusters = []
        themes = []
        pain_points = []
        for rc in raw_clusters:
            cid = str(uuid.uuid4())
            theme = rc.get("theme", "未命名主题")
            themes.append(theme)
            clusters.append({
                "id": cid,
                "member_ids": rc.get("member_ids", []),
                "theme": theme,
                "size": len(rc.get("member_ids", [])),
            })
            for pp in rc.get("pain_points", []):
                pain_points.append({
                    "topic": pp.get("topic", ""),
                    "severity": pp.get("severity", 3),
                    "evidence_count": len(rc.get("member_ids", [])),
                    "cluster_id": cid,
                })
        return {**state, "clusters": clusters, "themes": themes, "pain_points": pain_points}
    except Exception:
        logger.exception("ClusterNode LLM failed; fallback to rule-based mock")
        return cluster_node(state, gateway=None)
