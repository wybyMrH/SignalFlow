"""SignalFlow 后端 - 模型注册表。

支持多 provider（OpenAI / Azure / 文心一言 / Ollama / vLLM）动态注册与选择。
网关通过注册表解析 model alias → provider + 真实模型名 + 参数覆盖。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelConfig:
    """单一模型配置。"""

    provider: str
    model: str
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.2
    max_tokens: int = 2048
    timeout: int = 60
    extra: dict[str, Any] = field(default_factory=dict, repr=False)


class ProviderRegistry:
    """Provider 注册表（alias -> ModelConfig）。"""

    def __init__(self) -> None:
        self._store: dict[str, ModelConfig] = {}

    def register(self, alias: str, config: ModelConfig) -> None:
        """注册或覆盖模型别名。"""
        self._store[alias] = config

    def get(self, alias: str) -> ModelConfig:
        """获取配置；未知别名抛 KeyError。"""
        if alias not in self._store:
            raise KeyError(f"Model alias '{alias}' not registered")
        return self._store[alias]

    def remove(self, alias: str) -> None:
        """注销模型别名。"""
        self._store.pop(alias, None)

    def list_aliases(self) -> list[str]:
        """返回已注册别名列表。"""
        return list(self._store.keys())

    def build_model_name(self, alias: str) -> str:
        """构造 litellm 可识别的模型名 ``provider/model``。"""
        cfg = self.get(alias)
        return f"{cfg.provider}/{cfg.model}"


# 全局注册表（单例，应用启动时填充）
_registry = ProviderRegistry()


def get_registry() -> ProviderRegistry:
    """返回全局注册表单例。"""
    return _registry
