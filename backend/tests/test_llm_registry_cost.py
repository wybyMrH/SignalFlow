"""SignalFlow 后端 - 模型注册表与成本追踪单元测试。"""

from __future__ import annotations

import pytest

from app.llm.cost_tracker import CostTracker
from app.llm.registry import ModelConfig, ProviderRegistry, get_registry


def test_registry_register_get_remove():
    reg = ProviderRegistry()
    cfg = ModelConfig(provider="openai", model="gpt-4o-mini")
    reg.register("mini", cfg)
    assert reg.get("mini") is cfg
    assert reg.list_aliases() == ["mini"]
    assert reg.build_model_name("mini") == "openai/gpt-4o-mini"
    reg.remove("mini")
    assert reg.list_aliases() == []


def test_registry_get_unknown_raises():
    reg = ProviderRegistry()
    with pytest.raises(KeyError):
        reg.get("nope")


def test_registry_singleton_consistent():
    assert get_registry() is get_registry()


def test_cost_tracker_calculation():
    tracker = CostTracker()
    tracker.set_pricing("openai/gpt-4o-mini", input_price=0.00015, output_price=0.0006)
    tracker.track(
        request_id="r1",
        model="openai/gpt-4o-mini",
        prompt_tokens=1000,
        completion_tokens=1000,
        workflow="dedup",
    )
    record = tracker._records[0]
    assert record.total_tokens == 2000
    # 1000/1000 * 0.00015 + 1000/1000 * 0.0006 = 0.00075
    assert record.estimated_cost_usd == pytest.approx(0.00075)


def test_cost_tracker_summary_by_workflow():
    tracker = CostTracker()
    tracker.track(request_id="1", model="m", prompt_tokens=10, completion_tokens=10, workflow="a")
    tracker.track(request_id="2", model="m", prompt_tokens=20, completion_tokens=20, workflow="b")
    assert tracker.summary(workflow="a") == {"calls": 1, "total_tokens": 20, "total_cost_usd": 0.0}
    assert tracker.summary()["calls"] == 2
    assert tracker.summary()["total_tokens"] == 60


def test_cost_tracker_reset():
    tracker = CostTracker()
    tracker.track(request_id="1", model="m")
    tracker.reset()
    assert tracker._records == []
    assert tracker.summary()["calls"] == 0


def test_unknown_model_pricing_zero():
    tracker = CostTracker()
    record = tracker.track(request_id="1", model="unknown/model", prompt_tokens=100, completion_tokens=100)
    assert record.estimated_cost_usd == 0.0