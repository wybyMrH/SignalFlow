"""SignalFlow 后端 - 渠道适配器（集成层）。

定义外部反馈渠道的统一接入契约：工单系统、邮件、应用商店评论、
访谈纪要、政务热线等渠道各自实现 ChannelAdapter，注册进渠道注册表。
骨架阶段仅提供接口与注册表骨架。
"""

from abc import ABC, abstractmethod
from typing import Protocol

from app.schemas.feedback import FeedbackCreate


class ChannelAdapter(Protocol):
    """渠道适配器协议：将渠道原始数据规范化为 FeedbackCreate。"""

    channel: str

    def fetch_new(self, *, limit: int = 100) -> list[FeedbackCreate]:
        """拉取该渠道新增反馈。"""
        ...


class BaseChannelAdapter(ABC):
    """渠道适配器基类：统一渠道标识与拉取契约。"""

    channel: str = "base"

    def __init__(self, tenant_id: str = "default") -> None:
        self.tenant_id = tenant_id

    @abstractmethod
    def fetch_new(self, *, limit: int = 100) -> list[FeedbackCreate]:
        """子类实现：连接渠道、解析原始数据并返回规范化反馈。"""
        raise NotImplementedError


class ChannelRegistry:
    """渠道注册表：按渠道名取适配器，供收集服务动态分发。"""

    def __init__(self) -> None:
        self._adapters: dict[str, ChannelAdapter] = {}

    def register(self, adapter: ChannelAdapter) -> None:
        self._adapters[adapter.channel] = adapter

    def get(self, channel: str) -> ChannelAdapter | None:
        return self._adapters.get(channel)

    def all_channels(self) -> list[str]:
        return list(self._adapters.keys())


channel_registry = ChannelRegistry()