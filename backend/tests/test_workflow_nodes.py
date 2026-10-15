"""SignalFlow 后端 - 工作流节点单元测试。

每个节点分别覆盖规则路径（gateway=None/禁用）与 LLM 路径（注入 fake gateway），
并断言输出结构在两种模式之间保持一致的关键字段。
"""

from __future__ import annotations

from app.workflows.nodes import (
    cluster_node,
    dedup_node,
    draft_node,
    eval_node,
    priority_node,
)

# 10 条 mock 反馈（其中 2 对语义相近）
_IDS = [f"fb-{i}" for i in range(10)]
_CONTENTS = [
    "页面加载非常慢",
    "登录后页面加载慢",
    "导出 Excel 报错",
    "导出功能崩溃",
    "希望支持深色模式",
    "想要夜间模式",
    "移动端布局错乱",
    "手机上看按钮错位",
    "搜索不准确",
    "搜索结果相关度低",
]

_BASE_STATE = {
    "feedback_ids": _IDS,
    "contents": _CONTENTS,
    "tenant_id": "t1",
}


class _FakeGateway:
    """模拟 LLM 网关：仅标记 enabled；不真正发请求。"""

    enabled = True

    def __init__(self, *, structured: dict | None = None, embeddings: list[list[float]] | None = None) -> None:
        self._structured = structured or {}
        self._embeddings = embeddings

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self._embeddings is None:
            raise AssertionError("embed 不应在未配置 embeddings 时被调用")
        return self._embeddings

    def complete_structured(self, messages, *, workflow: str | None = None) -> dict:
        return self._structured


# ──────────────────────────────────────────────
# dedup_node
# ──────────────────────────────────────────────


def test_dedup_rule_mode_singleton_groups():
    state = dedup_node(dict(_BASE_STATE), gateway=None)
    assert state["dedup_groups"] == [[i] for i in _IDS]


def test_dedup_empty_input():
    state = dedup_node({"feedback_ids": [], "contents": []}, gateway=None)
    assert state["dedup_groups"] == []


def test_dedup_embedding_mode_groups_similar():
    # 1.0 表示完全相同；构造两组完全一样、其余独立
    import numpy as np

    emb: list[list[float]] = []
    for i in range(10):
        v = np.zeros(8)
        v[i % 2] = 1.0  # fb-0/2/4/6/8 相同 -> 一组；fb-1/3/5/7/9 相同 -> 二组
        emb.append(v.tolist())
    state = dedup_node(dict(_BASE_STATE), gateway=_FakeGateway(embeddings=emb))
    assert len(state["dedup_groups"]) == 2
    assert len(state["dedup_groups"][0]) == 5
    assert len(state["dedup_groups"][1]) == 5


def test_dedup_embedding_failure_falls_back():
    class _FailingGateway:
        enabled = True

        def embed(self, texts):
            raise RuntimeError("embedding down")

    state = dedup_node(dict(_BASE_STATE), gateway=_FailingGateway())
    assert state["dedup_groups"] == [[i] for i in _IDS]


# ──────────────────────────────────────────────
# cluster_node
# ──────────────────────────────────────────────


def test_cluster_rule_mode_structure():
    state = cluster_node(dict(_BASE_STATE, dedup_groups=[[_IDS[0], _IDS[1]], [_IDS[2]]]), gateway=None)
    assert len(state["clusters"]) == 2
    assert len(state["themes"]) == 2
    assert len(state["pain_points"]) == 2
    first = state["clusters"][0]
    assert first["member_ids"] == [_IDS[0], _IDS[1]]
    assert first["size"] == 2
    assert state["pain_points"][0]["cluster_id"] == first["id"]
    # 规则主题命名
    assert state["themes"][0] == "主题-1"


def test_cluster_empty_groups():
    state = cluster_node(dict(_BASE_STATE, dedup_groups=[]), gateway=None)
    assert state["clusters"] == []
    assert state["themes"] == []
    assert state["pain_points"] == []


def test_cluster_llm_mode_parses_result():
    fake = _FakeGateway(structured={
        "clusters": [
            {
                "theme": "性能问题",
                "member_ids": [_IDS[0], _IDS[1]],
                "pain_points": [{"topic": "加载速度", "severity": 4}],
            }
        ]
    })
    state = cluster_node(dict(_BASE_STATE, dedup_groups=[[_IDS[0], _IDS[1]]]), gateway=fake)
    assert state["themes"] == ["性能问题"]
    assert state["clusters"][0]["theme"] == "性能问题"
    assert state["pain_points"][0]["topic"] == "加载速度"
    assert state["pain_points"][0]["severity"] == 4


# ──────────────────────────────────────────────
# eval_node
# ──────────────────────────────────────────────


def test_eval_rule_mode_scoring():
    pain_points = [
        {"topic": "加载速度", "severity": 5, "evidence_count": 4},
        {"topic": "导出报错", "severity": 2, "evidence_count": 1},
    ]
    state = eval_node(dict(_BASE_STATE, pain_points=pain_points), gateway=None)
    assessments = state["impact_assessments"]
    assert len(assessments) == 2
    # severity*10 + evidence*5 = 5*10 + 4*5 = 70
    assert assessments[0]["impact_score"] == 70
    # customer_value = min(100, 40 + evidence*8) = 40 + 32 = 72
    assert assessments[0]["customer_value"] == 72
    # confidence = min(1.0, 0.5 + evidence*0.05) = 0.5 + 0.2 = 0.7
    assert assessments[0]["confidence"] == 0.7


def test_eval_empty_pain_points():
    state = eval_node(dict(_BASE_STATE, pain_points=[]), gateway=None)
    assert state["impact_assessments"] == []


def test_eval_llm_mode_keeps_boundaries():
    fake = _FakeGateway(structured={
        "assessments": [
            {"topic": "性能", "impact_score": 500, "customer_value": 200, "confidence": 9.0}
        ]
    })
    state = eval_node(dict(_BASE_STATE, pain_points=[{"topic": "性能", "severity": 3, "evidence_count": 2}]), gateway=fake)
    a = state["impact_assessments"][0]
    assert a["impact_score"] == 100
    assert a["customer_value"] == 100
    assert a["confidence"] == 1.0


# ──────────────────────────────────────────────
# priority_node
# ──────────────────────────────────────────────


def test_priority_rule_mode_sorts_and_decides():
    assessments = [
        {"topic": "低", "impact_score": 30, "customer_value": 40, "confidence": 0.5},
        {"topic": "高", "impact_score": 90, "customer_value": 90, "confidence": 0.9},
    ]
    state = priority_node(dict(_BASE_STATE, impact_assessments=assessments), gateway=None)
    assert [p["topic"] for p in state["priorities"]] == ["高", "低"]
    # rank 按降序编号
    assert state["priorities"][0]["rank"] == 1
    # 高 -> 90*0.9=81 >= 60 跟进；低 -> 30*0.5=15 < 60 不跟进
    assert [d["topic"] for d in state["decisions"]] == ["高"]


def test_priority_empty_assessments():
    state = priority_node(dict(_BASE_STATE, impact_assessments=[]), gateway=None)
    assert state["priorities"] == []
    assert state["decisions"] == []


# ──────────────────────────────────────────────
# draft_node
# ──────────────────────────────────────────────


def test_draft_rule_mode_template():
    decisions = [{"topic": "性能", "action": "跟进", "confidence": 0.8}]
    state = draft_node(dict(_BASE_STATE, decisions=decisions), gateway=None)
    drafts = state["reply_drafts"]
    assert len(drafts) == 1
    assert "性能" in drafts[0]["content"]
    assert drafts[0]["priority"] == 80


def test_draft_empty_decisions():
    state = draft_node(dict(_BASE_STATE, decisions=[]), gateway=None)
    assert state["reply_drafts"] == []


def test_draft_llm_mode():
    fake = _FakeGateway(structured={
        "drafts": [
            {"content": "已转交性能团队", "target_feedback_ids": [_IDS[0]], "priority": 95, "topic": "性能"}
        ]
    })
    state = draft_node(dict(_BASE_STATE, decisions=[{"topic": "性能", "action": "跟进", "confidence": 0.8}]), gateway=fake)
    assert state["reply_drafts"][0]["content"] == "已转交性能团队"
    assert state["reply_drafts"][0]["priority"] == 95