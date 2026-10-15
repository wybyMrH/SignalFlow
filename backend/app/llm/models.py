"""SignalFlow 后端 - LLM 输出模型与结构化解析。

统一 JSON mode / function calling 的解析与校验；上层不直接处理
litellm 返回的原始 dict，只依赖本网关输出的结构化对象。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LLMResponse:
    """标准化 LLM 补全结果。"""

    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


class StructuredOutputError(RuntimeError):
    """结构化输出解析失败。"""


class LLMGatewayError(RuntimeError):
    """LLM 网关统一异常。"""


def parse_json_output(content: str) -> dict[str, Any]:
    """从 LLM 返回文本中提取 JSON 对象。

    兼容两种情况：
    1. 纯 JSON 字符串；
    2. Markdown 代码块 ```json ... ``` 包裹。
    """
    text = content.strip()
    if text.startswith("```"):
        # 去掉首行 ```json 与末行 ```
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning("JSON parse failed: %s", exc)
        raise StructuredOutputError(f"JSON parse failed: {exc}") from exc


def safe_extract_field(data: dict[str, Any], *paths: str, default: Any = None) -> Any:
    """按候选路径顺序提取字段；均缺失时返回 default。"""
    for p in paths:
        if p in data:
            return data[p]
    return default
