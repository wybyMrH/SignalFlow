"""SignalFlow 后端 - LLM 调用成本追踪。

按请求/模型/工作流维度记录 token 用量与估算费用，便于预算告警与优化。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


# 粗略单价（USD / 1K tokens）；生产期应从配置或外部服务获取
_DEFAULT_PRICING: dict[str, dict[str, float]] = {
    "openai/gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "openai/gpt-4o": {"input": 0.0025, "output": 0.01},
    "openai/text-embedding-3-small": {"input": 0.00002, "output": 0.0},
    "azure/gpt-4o": {"input": 0.0025, "output": 0.01},
}


@dataclass
class CostRecord:
    """单次调用成本记录。"""

    request_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    workflow: str | None = None
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    meta: dict[str, Any] = field(default_factory=dict, repr=False)


class CostTracker:
    """内存成本追踪器（生产期可换写数据库/指标系统）。"""

    def __init__(self) -> None:
        self._records: list[CostRecord] = []
        self._pricing: dict[str, dict[str, float]] = dict(_DEFAULT_PRICING)

    def set_pricing(self, model: str, input_price: float, output_price: float) -> None:
        """设置/覆盖模型单价。"""
        self._pricing[model] = {"input": input_price, "output": output_price}

    def track(
        self,
        *,
        request_id: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        workflow: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> CostRecord:
        """记录一次调用并返回成本记录。"""
        pricing = self._pricing.get(model, {"input": 0.0, "output": 0.0})
        cost = (
            prompt_tokens / 1000 * pricing["input"]
            + completion_tokens / 1000 * pricing["output"]
        )
        record = CostRecord(
            request_id=request_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost_usd=round(cost, 6),
            workflow=workflow,
            meta=meta or {},
        )
        self._records.append(record)
        logger.info(
            "Cost tracked: %s | model=%s tokens=%s cost=$%s",
            request_id,
            model,
            record.total_tokens,
            record.estimated_cost_usd,
        )
        return record

    def summary(self, *, workflow: str | None = None) -> dict[str, Any]:
        """返回累计统计。"""
        records = self._records
        if workflow:
            records = [r for r in records if r.workflow == workflow]
        total_tokens = sum(r.total_tokens for r in records)
        total_cost = sum(r.estimated_cost_usd for r in records)
        return {
            "calls": len(records),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
        }

    def reset(self) -> None:
        """清空记录（仅用于测试）。"""
        self._records.clear()
