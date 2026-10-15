"""SignalFlow 后端 - LLM 网关单元测试。

覆盖：网关禁用时短路、JSON mode 结构化解析、主/次模型 fallback、
成本追踪联动。所有测试使用 monkeypatch 替换 litellm.completion，
不发起真实外部调用。
"""

from __future__ import annotations

import importlib
import sys

import pytest

from app.core.config import settings as app_settings
from app.llm.gateway import LLMGateway
from app.llm.models import LLMGatewayError, StructuredOutputError, parse_json_output, safe_extract_field
from app.llm.cost_tracker import CostTracker
from app.llm.registry import ProviderRegistry

# NOTE: app.llm.__init__ 导出模块级单例 gateway，会遮蔽子模块名 app.llm.gateway。
# 这里必须经 sys.modules 取真模块，否则 monkeypatch.setattr 会作用到实例上。
gateway_mod = sys.modules["app.llm.gateway"]


class _FakeUsage:
    """模拟 litellm usage 对象。"""

    def __init__(self, prompt_tokens: int = 10, completion_tokens: int = 20) -> None:
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


class _FakeChoice:
    """模拟 litellm choice 对象。"""

    def __init__(self, content: str) -> None:
        self.finish_reason = "stop"
        self.message = _FakeMessage(content)


class _FakeMessage:
    """模拟 litellm message 对象。"""

    def __init__(self, content: str) -> None:
        self.content = content


class _FakeResp:
    """模拟 litellm completion 响应。"""

    def __init__(self, content: str, *, model: str = "openai/gpt-4o-mini") -> None:
        self.id = "req-1"
        self.choices = [_FakeChoice(content)]
        self.usage = _FakeUsage()


def _build_gateway(monkeypatch, *, enabled: bool = True, fallback_model: str | None = "openai/gpt-4o"):
    monkeypatch.setattr(app_settings, "workflow_llm_enabled", enabled)
    monkeypatch.setattr(app_settings, "llm_fallback_model", fallback_model)
    monkeypatch.setattr(app_settings, "llm_model", "gpt-4o-mini")
    monkeypatch.setattr(app_settings, "llm_provider", "openai")
    monkeypatch.setattr(app_settings, "llm_api_key", "test-key")
    tracker = CostTracker()
    gateway = LLMGateway(cost_tracker=tracker)
    return gateway, tracker


def test_gateway_disabled_returns_empty(monkeypatch):
    """网关禁用时 complete/complete_structured/embed 均短路返回空值。"""
    gateway, _ = _build_gateway(monkeypatch, enabled=False)
    assert gateway.complete([{"role": "user", "content": "hi"}]) == ""
    assert gateway.complete_structured([{"role": "user", "content": "hi"}]) == {}
    assert gateway.embed(["a"]) == []


def test_complete_returns_text_and_tracks_cost(monkeypatch):
    """启用时 complete 返回 content 并记录成本。"""
    gateway, tracker = _build_gateway(monkeypatch, enabled=True)
    monkeypatch.setattr(gateway_mod, "completion", lambda **kwargs: _FakeResp("你好，SignalFlow！"))
    text = gateway.complete([{"role": "user", "content": "hi"}], workflow="test")
    assert text == "你好，SignalFlow！"
    summary = tracker.summary(workflow="test")
    assert summary["calls"] == 1
    assert summary["total_tokens"] == 30
    assert summary["total_cost_usd"] > 0


def test_complete_structured_parses_json(monkeypatch):
    """JSON mode 下返回解析后的 dict。"""
    gateway, _ = _build_gateway(monkeypatch, enabled=True)
    payload = '{"clusters": [{"theme": "性能", "member_ids": ["1"]}]}'
    monkeypatch.setattr(gateway_mod, "completion", lambda **kwargs: _FakeResp(payload))
    result = gateway.complete_structured([{"role": "user", "content": "x"}], workflow="cluster")
    assert result["clusters"][0]["theme"] == "性能"


def test_complete_structured_parses_markdown_codeblock(monkeypatch):
    """兼容 ```json 代码块包裹。"""
    gateway, _ = _build_gateway(monkeypatch, enabled=True)
    payload = '```json\n{"ok": true}\n```'
    monkeypatch.setattr(gateway_mod, "completion", lambda **kwargs: _FakeResp(payload))
    result = gateway.complete_structured([{"role": "user", "content": "x"}])
    assert result == {"ok": True}


def test_complete_fallback_on_primary_failure(monkeypatch):
    """主模型失败后自动降级到 fallback 模型。"""
    gateway, tracker = _build_gateway(monkeypatch, enabled=True, fallback_model="openai/gpt-4o")

    calls: list[str] = []

    def _flaky(**kwargs):
        calls.append(kwargs["model"])
        if kwargs["model"] == "openai/gpt-4o-mini":
            raise RuntimeError("primary down")
        return _FakeResp("fallback ok", model="openai/gpt-4o")

    monkeypatch.setattr(gateway_mod, "completion", _flaky)
    text = gateway.complete([{"role": "user", "content": "x"}])
    assert text == "fallback ok"
    assert calls == ["openai/gpt-4o-mini", "openai/gpt-4o"]
    assert tracker.summary()["calls"] == 1


def test_complete_raises_when_all_fail(monkeypatch):
    """主备均失败时抛 LLMGatewayError。"""
    gateway, _ = _build_gateway(monkeypatch, enabled=True)

    def _always_fail(**kwargs):
        raise RuntimeError("down")

    monkeypatch.setattr(gateway_mod, "completion", _always_fail)
    with pytest.raises(LLMGatewayError):
        gateway.complete([{"role": "user", "content": "x"}])


def test_embed_returns_vectors(monkeypatch):
    """embed 返回向量列表；禁用时返回空列表。"""
    gateway, _ = _build_gateway(monkeypatch, enabled=True)

    class _Data:
        data = [{"embedding": [0.1, 0.2]}, {"embedding": [0.3, 0.4]}]

    monkeypatch.setattr(gateway_mod, "embedding", lambda **kwargs: _Data())
    vectors = gateway.embed(["a", "b"])
    assert vectors == [[0.1, 0.2], [0.3, 0.4]]


def test_register_provider_alias_and_model_name(monkeypatch):
    """动态注册 provider alias 后模型名按 provider/model 解析。"""
    from app.llm.registry import ModelConfig

    gateway, _ = _build_gateway(monkeypatch, enabled=True)
    gateway.register_provider("ernie", ModelConfig(provider="baidu", model="ernie-4.0"))
    # 含 / 直接使用；alias 走注册表
    assert gateway._model_name("ernie") == "baidu/ernie-4.0"
    assert gateway._model_name("openai/gpt-4o") == "openai/gpt-4o"


# ──────────────────────────────────────────────
# models 模块纯函数
# ──────────────────────────────────────────────


def test_parse_json_output_plain_and_codeblock():
    assert parse_json_output('{"a": 1}') == {"a": 1}
    assert parse_json_output('```json\n{"a": 2}\n```') == {"a": 2}


def test_parse_json_output_invalid_raises():
    with pytest.raises(StructuredOutputError):
        parse_json_output("not json")


def test_safe_extract_field_paths():
    data = {"a": {"b": 1}}
    assert safe_extract_field(data, "a") == {"b": 1}
    assert safe_extract_field(data, "missing", "a") == {"b": 1}
    assert safe_extract_field(data, "missing", default="x") == "x"