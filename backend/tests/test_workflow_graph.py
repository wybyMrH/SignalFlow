"""SignalFlow 后端 - 工作流图端到端与 checkpoint 集成测试。

规则模式（LLM 关闭）端到端：10 条 mock 反馈全链路执行并断言输出；
checkpoint 持久化：使用独立测试 PostgreSQL（container:5433）验证
中断后可恢复状态。
"""

from __future__ import annotations

import os

import pytest

from app.workflows import build_analysis_graph
from app.workflows.state import FeedbackAnalysisState

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

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://signalflow:signalflow@localhost:5433/signalflow",
)


def _run_graph(graph, *, config: dict | None = None) -> dict:
    result = graph.invoke(
        {
            "feedback_ids": _IDS,
            "contents": _CONTENTS,
            "tenant_id": "t1",
        },
        config=config,
    )
    return dict(result)


# ──────────────────────────────────────────────
# 图结构与端到端（规则模式）
# ──────────────────────────────────────────────


def test_build_graph_returns_stategraph():
    graph = build_analysis_graph()
    assert graph is not None
    compiled = graph.compile()
    assert compiled is not None


def test_e2e_rule_mode_full_pipeline():
    """10 条反馈规则模式端到端：输出结构完整且数量自洽。"""
    graph = build_analysis_graph().compile()
    result = _run_graph(graph)

    assert len(result["dedup_groups"]) == 10  # 规则模式：单元素分组
    assert len(result["clusters"]) == 10
    assert len(result["themes"]) == 10
    assert len(result["pain_points"]) == 10
    assert len(result["impact_assessments"]) == 10
    assert len(result["priorities"]) == 10
    # 规则评分：severity=3, evidence=1 -> impact=35; 35*confidence(0.55)=19 < 60
    assert result["decisions"] == []
    assert result["reply_drafts"] == []


def test_e2e_rule_mode_decisions_trigger_with_high_severity():
    """提高 severity/evidence 后应产生决策与草稿，验证节点联动。"""
    state = {
        "feedback_ids": _IDS,
        "contents": _CONTENTS,
        "tenant_id": "t1",
        # 手工注入高严重度痛点以触发决策
        "pain_points": [
            {"topic": "加载严重缓慢", "severity": 5, "evidence_count": 6},
            {"topic": "导出崩溃", "severity": 5, "evidence_count": 5},
        ],
    }
    # 从 eval 开始走链路的其余部分：直接调用 graph 需要完整输入，
    # 因此这里单独验证 priority -> draft 联动
    from app.workflows.nodes import draft_node, eval_node, priority_node

    evaluated = eval_node(state, gateway=None)
    prioritized = priority_node(evaluated, gateway=None)
    drafted = draft_node(prioritized, gateway=None)

    # severity=5,evidence=6 -> impact=80; 80*0.8=64 >= 60 -> 跟进
    assert len(prioritized["decisions"]) == 1
    assert prioritized["decisions"][0]["action"] == "跟进"
    assert len(drafted["reply_drafts"]) == 1


def test_graph_invocation_uses_module_level_instance():
    """模块级 analysis_graph 可直接 invoke。"""
    from app.workflows import analysis_graph

    result = analysis_graph.invoke(
        {
            "feedback_ids": _IDS[:3],
            "contents": _CONTENTS[:3],
            "tenant_id": "t1",
        }
    )
    assert result["dedup_groups"]
    assert result["clusters"]


# ──────────────────────────────────────────────
# checkpoint 持久化（PostgreSQL 集成）
# ──────────────────────────────────────────────


@pytest.mark.integration
def test_checkpoint_persistence_and_resume():
    """使用测试库保存 checkpoint 并从已保存状态恢复。

    通过注入普通 psycopg 连接绕过 ConnectionPool（其后台线程在部分
    沙箱环境中无法调度），仅验证 PostgresSaver 持久化能力本身。
    """
    import psycopg

    from app.workflows.checkpoint import get_checkpointer, setup_checkpoint

    conn = psycopg.connect(
        "host=localhost port=5433 user=signalflow password=signalflow dbname=signalflow",
        connect_timeout=10,
    )
    try:
        setup_checkpoint(conn=conn)
        checkpointer = get_checkpointer(conn=conn)
        graph = build_analysis_graph().compile(checkpointer=checkpointer)

        thread_id = "thread-e2e-1"
        first = graph.invoke(
            {
                "feedback_ids": _IDS,
                "contents": _CONTENTS,
                "tenant_id": "t1",
            },
            config={"configurable": {"thread_id": thread_id}},
        )
        # 恢复同一 thread 的完整状态
        resumed = graph.get_state({"configurable": {"thread_id": thread_id}})
        assert resumed is not None
        saved_state = dict(resumed.values or {})
        assert saved_state["feedback_ids"] == _IDS
        assert saved_state["dedup_groups"] == first["dedup_groups"]
        assert saved_state["clusters"] == first["clusters"]
    finally:
        conn.close()