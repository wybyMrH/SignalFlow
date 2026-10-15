"""SignalFlow 后端 - LiteLLM 网关层。

统一所有 LLM/Embedding 调用入口：provider 切换、模型路由、密钥注入、
超时与降级。上层（workflows/services）只依赖本网关，不直接接触 litellm API。

骨架阶段提供完整封装签名；真实调用默认由开关控制，便于离线开发与测试。
"""

from __future__ import annotations

from typing import Any

from litellm import completion, embedding

from app.core.config import settings
from app.core.logging import get_logger
from app.llm.cost_tracker import CostTracker, CostRecord
from app.llm.models import LLMGatewayError, LLMResponse, StructuredOutputError, parse_json_output
from app.llm.registry import ModelConfig, ProviderRegistry, get_registry

logger = get_logger(__name__)


class LLMGateway:
    """LiteLLM 统一接入网关。

    支持：
    - 主/次模型自动降级（fallback）；
    - 注册表多 provider 切换；
    - 结构化 JSON mode 输出解析；
    - Token 用量追踪（cost_tracker 注入）。
    """

    def __init__(
        self,
        *,
        registry: ProviderRegistry | None = None,
        cost_tracker: CostTracker | None = None,
    ) -> None:
        self.provider = settings.llm_provider
        self.model = settings.llm_model
        self.api_key = settings.llm_api_key
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.timeout = settings.llm_timeout_seconds
        self.fallback_model = settings.llm_fallback_model
        self.enabled = settings.workflow_llm_enabled
        self._registry = registry or get_registry()
        self._cost = cost_tracker or CostTracker()

    # ──────────────────────────────────────────────
    # 内部辅助
    # ──────────────────────────────────────────────

    def _model_name(self, model: str | None) -> str:
        """解析 LiteLLM 模型名。

        优先级：
        1. 若 model 含 ``/`` 直接使用（已含 provider）；
        2. 若 model 是注册表 alias，用注册表构造 ``provider/model``；
        3. 否则使用 settings 中的 ``provider/model``。
        """
        if not model:
            return f"{self.provider}/{self.model}"
        if "/" in model:
            return model
        try:
            return self._registry.build_model_name(model)
        except KeyError:
            return f"{self.provider}/{model}"

    def _call_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict[str, str] | None = None,
    ) -> Any:
        """底层 completion 调用，返回 litellm 原始响应对象。"""
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "api_key": self.api_key,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            "timeout": self.timeout,
        }
        if response_format is not None:
            kwargs["response_format"] = response_format
        return completion(**kwargs)

    def _track_usage(self, resp: Any, *, model: str, workflow: str | None = None) -> CostRecord | None:
        """从 litellm 响应中提取 usage 并记录成本。"""
        try:
            usage = getattr(resp, "usage", None) or {}
            record = self._cost.track(
                request_id=getattr(resp, "id", "unknown"),
                model=model,
                prompt_tokens=getattr(usage, "prompt_tokens", 0) or usage.get("prompt_tokens", 0),
                completion_tokens=getattr(usage, "completion_tokens", 0) or usage.get("completion_tokens", 0),
                workflow=workflow,
                meta={"finish_reason": getattr(resp.choices[0], "finish_reason", None)},
            )
            return record
        except Exception:
            logger.warning("Usage tracking failed", exc_info=True)
            return None

    # ──────────────────────────────────────────────
    # 公开接口
    # ──────────────────────────────────────────────

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        workflow: str | None = None,
    ) -> str:
        """调用 LLM 补全。返回文本内容；失败抛 LLMGatewayError（上层降级）。"""
        if not self.enabled:
            logger.warning("LLM gateway disabled; skip completion call")
            return ""
        model_name = self._model_name(model)
        try:
            resp = self._call_completion(model_name, messages, temperature=temperature, max_tokens=max_tokens)
            self._track_usage(resp, model=model_name, workflow=workflow)
            text = resp.choices[0].message.content  # type: ignore[index]
            return str(text)
        except Exception as exc:  # noqa: BLE001 - 网关须兜底所有上游错误
            logger.exception("LLM completion failed: %s", exc)
            if self.fallback_model:
                fallback_name = self._model_name(self.fallback_model)
                try:
                    resp = self._call_completion(fallback_name, messages, temperature=temperature, max_tokens=max_tokens)
                    self._track_usage(resp, model=fallback_name, workflow=workflow)
                    return str(resp.choices[0].message.content)  # type: ignore[index]
                except Exception as fallback_exc:  # noqa: BLE001
                    raise LLMGatewayError(f"LLM fallback failed: {fallback_exc}") from fallback_exc
            raise LLMGatewayError(f"LLM completion failed: {exc}") from exc

    def complete_structured(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        workflow: str | None = None,
    ) -> dict[str, Any]:
        """调用 LLM JSON mode 并解析为 dict；解析失败抛 StructuredOutputError。"""
        if not self.enabled:
            logger.warning("LLM gateway disabled; skip structured completion")
            return {}
        model_name = self._model_name(model)
        try:
            resp = self._call_completion(
                model_name,
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            self._track_usage(resp, model=model_name, workflow=workflow)
            text = resp.choices[0].message.content  # type: ignore[index]
            return parse_json_output(str(text))
        except (StructuredOutputError, LLMGatewayError):
            raise
        except Exception as exc:  # noqa: BLE001
            raise LLMGatewayError(f"LLM structured completion failed: {exc}") from exc

    def embed(self, texts: list[str]) -> list[list[float]]:
        """批量 Embedding（去重/聚类前置）。失败抛 LLMGatewayError。"""
        if not self.enabled:
            logger.warning("LLM gateway disabled; skip embedding call")
            return []
        model_name = f"{settings.embedding_provider}/{settings.embedding_model}"
        try:
            resp = embedding(
                model=model_name,
                input=texts,
                api_key=settings.embedding_api_key,
                timeout=self.timeout,
            )
            return [item["embedding"] for item in resp.data]  # type: ignore[union-attr]
        except Exception as exc:  # noqa: BLE001
            logger.exception("Embedding failed: %s", exc)
            raise LLMGatewayError(f"Embedding failed: {exc}") from exc

    # ──────────────────────────────────────────────
    # 配置快捷方法
    # ──────────────────────────────────────────────

    def register_provider(self, alias: str, config: ModelConfig) -> None:
        """向注册表动态注册 provider/model 别名。"""
        self._registry.register(alias, config)

    def summary(self, *, workflow: str | None = None) -> dict[str, Any]:
        """返回 LLM 调用成本统计。"""
        return self._cost.summary(workflow=workflow)


gateway = LLMGateway()