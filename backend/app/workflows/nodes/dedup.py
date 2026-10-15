"""去重节点（DedupNode）。

输入：feedback_ids + contents
输出：dedup_groups（相似反馈 id 的分组列表）

LLM 启用时：基于 Embedding 余弦相似度阈值（默认 0.85）分组；
禁用时：每个 id 自成一组（无重复假设）。
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from app.core.logging import get_logger
from app.workflows.state import FeedbackAnalysisState

if TYPE_CHECKING:
    from app.llm.gateway import LLMGateway

logger = get_logger(__name__)

_DEFAULT_THRESHOLD = 0.85


def _cosine(a: list[float], b: list[float]) -> float:
    """计算两个向量余弦相似度。"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _greedy_group(ids: list[str], embeddings: list[list[float]], threshold: float = _DEFAULT_THRESHOLD) -> list[list[str]]:
    """贪心合并：每条反馈依次与已创建组的代表向量比对，决定加入或新建组。"""
    if not ids:
        return []
    groups: list[list[str]] = []
    reps: list[list[float]] = []
    for fid, emb in zip(ids, embeddings):
        placed = False
        for idx, rep in enumerate(reps):
            if _cosine(emb, rep) >= threshold:
                groups[idx].append(fid)
                placed = True
                break
        if not placed:
            groups.append([fid])
            reps.append(emb)
    return groups


def dedup_node(
    state: FeedbackAnalysisState,
    *,
    gateway: "LLMGateway | None" = None,
    threshold: float = _DEFAULT_THRESHOLD,
) -> FeedbackAnalysisState:
    """去重节点。

    当 ``gateway`` 为 None 或未启用时返回单元素分组；
    启用时基于 Embedding 贪心分组。
    """
    ids = state.get("feedback_ids", [])
    contents = state.get("contents", [])
    if not ids:
        return {**state, "dedup_groups": []}

    if gateway is None or not gateway.enabled:
        logger.info("DedupNode: LLM disabled, singleton groups")
        return {**state, "dedup_groups": [[i] for i in ids]}

    # 真实 Embedding 分组
    try:
        embeddings = gateway.embed(contents)
    except Exception:
        logger.exception("Embedding failed in dedup_node; fallback to singletons")
        return {**state, "dedup_groups": [[i] for i in ids]}

    if not embeddings:
        return {**state, "dedup_groups": [[i] for i in ids]}

    groups = _greedy_group(ids, embeddings, threshold=threshold)
    logger.info("DedupNode: %s items -> %s groups", len(ids), len(groups))
    return {**state, "dedup_groups": groups}
