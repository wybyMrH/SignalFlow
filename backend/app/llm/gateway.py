"""SignalFlow 后端 - LiteLLM 网关层。

统一所有 LLM/Embedding 调用入口：provider 切换、模型路由、密钥注入、
超时与降级。上层（workflows/services）只依赖本网关，不直接接触 litellm API。

骨架阶段提供完整封装签名；真实调用默认由开关控制，便于离线开发与测试。
"""


from litellm import completion, embedding

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMGatewayError(RuntimeError):
    """LLM 网关统一异常。上层据此做降级/重试决策。"""


class LLMGateway:
    """LiteLLM 统一接入网关。"""

    def __init__(self) -> None:
        self.provider = settings.llm_provider
        self.model = settings.llm_model
        self.api_key = settings.llm_api_key
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.timeout = settings.llm_timeout_seconds
        self.fallback_model = settings.llm_fallback_model
        self.enabled = settings.workflow_llm_enabled

    def _model_name(self, model: str | None) -> str:
        """LiteLLM 模型名：litellm 支持 `provider/model` 或裸模型名。"""
        if "/" in (model or ""):
            return model  # type: ignore[return-value]
        return f"{self.provider}/{model}" if model else f"{self.provider}/{self.model}"

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """调用 LLM 补全。返回文本内容；失败抛 LLMGatewayError（上层降级）。"""
        if not self.enabled:
            logger.warning("LLM gateway disabled; skip completion call")
            return ""
        try:
            resp = completion(
                model=self._model_name(model),
                messages=messages,
                api_key=self.api_key,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                timeout=self.timeout,
            )
            text = resp.choices[0].message.content  # type: ignore[index]
            return str(text)
        except Exception as exc:  # noqa: BLE001 - 网关须兜底所有上游错误
            logger.exception("LLM completion failed: %s", exc)
            if self.fallback_model:
                try:
                    resp = completion(
                        model=self._model_name(self.fallback_model),
                        messages=messages,
                        api_key=self.api_key,
                        timeout=self.timeout,
                    )
                    return str(resp.choices[0].message.content)  # type: ignore[index]
                except Exception as fallback_exc:  # noqa: BLE001
                    raise LLMGatewayError(f"LLM fallback failed: {fallback_exc}") from fallback_exc
            raise LLMGatewayError(f"LLM completion failed: {exc}") from exc

    def embed(self, texts: list[str]) -> list[list[float]]:
        """批量 Embedding（去重/聚类前置）。失败抛 LLMGatewayError。"""
        if not self.enabled:
            logger.warning("LLM gateway disabled; skip embedding call")
            return []
        try:
            resp = embedding(
                model=f"{settings.embedding_provider}/{settings.embedding_model}",
                input=texts,
                api_key=settings.embedding_api_key,
                timeout=self.timeout,
            )
            return [item["embedding"] for item in resp.data]  # type: ignore[union-attr]
        except Exception as exc:  # noqa: BLE001
            logger.exception("Embedding failed: %s", exc)
            raise LLMGatewayError(f"Embedding failed: {exc}") from exc


gateway = LLMGateway()