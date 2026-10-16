"""SignalFlow 后端 - 渠道适配器（集成层）。

外部反馈渠道的统一接入契约，数据流如下：:

    外部原始数据(raw)
        │  BaseAdapter.parse()
        ▼
    统一反馈事件 (FeedbackEvent)
        │  BaseAdapter.normalize()
        ▼
    标准反馈 (StandardFeedback)
        │  InboundProcessor.process()
        ▼
    反馈表（DB）

设计约束：
- 适配器层不直接写数据库，只生产标准化事件（StandardFeedback）。
- 事件由统一的「入站处理器」消费并落库，处理器按 source_ref 幂等去重。
- 每个渠道的适配器独立注册进 ChannelRegistry；编排层（Ingestor）负责
  隔离单渠道异常，失败不影响主服务，错误记入独立日志通道。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Protocol

from pydantic import BaseModel, Field

from app.schemas.feedback import FeedbackCreate

# 渠道集成层独立日志通道（与业务日志分离，便于按渠道排查）
logger = logging.getLogger("signalflow.integrations")


class FeedbackEvent(BaseModel):
    """渠道原始数据解析后的统一反馈事件（中间表示）。

    - raw_content 为反馈原话（权威事实，适配器不得改写原文）。
    - source 为反馈来源类型（ticket/email/review/hotline...），用于前端筛选。
    - channel 为接入渠道系统标识（ticket_system/email/im/app_store/gov_hotline）。
    - metadata 保留渠道原始字段，供审计与后续扩展。
    """

    source: str = "manual"
    channel: str = "base"
    raw_content: str
    customer_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class StandardFeedback(BaseModel):
    """规范化后的标准反馈：可被入站处理器直接落库。

    source_ref 形如 ``{channel}:{external_id}``，作为幂等去重键，
    同一渠道的同一条外部记录不会重复入库。
    """

    source: str = "manual"
    source_ref: str | None = None
    content: str
    author: str | None = None
    customer_id: str | None = None
    channel: str = "base"
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_feedback_create(self) -> FeedbackCreate:
        """转换为仓储/服务层可用的 FeedbackCreate。"""
        return FeedbackCreate(
            source=self.source,
            source_ref=self.source_ref,
            content=self.content,
            author=self.author,
        )


class BaseAdapter(ABC):
    """渠道适配器基类：子类实现「拉取 → 解析 → 标准化」三段契约。

    必须实现：
        fetch_raw(raw 拉取)      —— 连接外部系统取回原始数据
        parse(raw → event)       —— 原始数据 → 统一反馈事件
        normalize(event → std)   —— 统一反馈事件 → 标准反馈
    """

    channel: str = "base"
    source: str = "manual"

    def __init__(self, *, tenant_id: str = "default") -> None:
        self.tenant_id = tenant_id

    @abstractmethod
    def fetch_raw(self, *, limit: int = 100) -> list[Any]:
        """连接渠道拉取原始数据（不解析）。"""
        raise NotImplementedError

    @abstractmethod
    def parse(self, raw: Any) -> FeedbackEvent:
        """将单条渠道原始数据解析为统一反馈事件。"""
        raise NotImplementedError

    @abstractmethod
    def normalize(self, event: FeedbackEvent) -> StandardFeedback:
        """将统一反馈事件规范化为标准反馈（不落库）。"""
        raise NotImplementedError

    def fetch_new(self, *, limit: int = 100) -> list[StandardFeedback]:
        """拉取 → 解析 → 标准化的完整链路，供入站编排器消费。"""
        result: list[StandardFeedback] = []
        for raw in self.fetch_raw(limit=limit):
            event = self.parse(raw)
            result.append(self.normalize(event))
        return result


class InboundProcessor(Protocol):
    """入站处理器协议：消费标准反馈并落库，返回反馈 id。"""

    def process(
        self, feedback: StandardFeedback, *, tenant_id: str = "default"
    ) -> str:
        """消费一条标准反馈；重复 source_ref 应幂等跳过并返回已存在 id。"""
        ...


class ChannelRegistry:
    """渠道注册表：按渠道名路由适配器，供入站编排器动态分发。"""

    def __init__(self) -> None:
        self._adapters: dict[str, BaseAdapter] = {}

    def register(self, adapter: BaseAdapter) -> None:
        if adapter.channel in self._adapters:
            logger.warning("渠道 %s 重复注册，覆盖旧适配器", adapter.channel)
        self._adapters[adapter.channel] = adapter

    def get(self, channel: str) -> BaseAdapter | None:
        return self._adapters.get(channel)

    def all_channels(self) -> list[str]:
        return list(self._adapters.keys())

    def all_adapters(self) -> list[BaseAdapter]:
        return list(self._adapters.values())


channel_registry = ChannelRegistry()