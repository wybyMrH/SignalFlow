"""SignalFlow 后端 - 渠道适配器与集成层。

对外暴露：
- 契约：FeedbackEvent / StandardFeedback / BaseAdapter / InboundProcessor
- 注册表：ChannelRegistry / channel_registry
- 内置渠道适配器：工单系统、邮件、IM、应用商店评论、政务热线
"""

from app.integrations.app_store import AppStoreAdapter
from app.integrations.base import (
    BaseAdapter,
    ChannelRegistry,
    FeedbackEvent,
    InboundProcessor,
    StandardFeedback,
    channel_registry,
)
from app.integrations.email import EmailAdapter
from app.integrations.gov_hotline import GovHotlineAdapter
from app.integrations.im import IMAdapter
from app.integrations.processor import FeedbackInboundProcessor, Ingestor
from app.integrations.ticket_system import TicketSystemAdapter

__all__ = [
    "BaseAdapter",
    "ChannelRegistry",
    "FeedbackEvent",
    "InboundProcessor",
    "StandardFeedback",
    "channel_registry",
    "TicketSystemAdapter",
    "EmailAdapter",
    "IMAdapter",
    "AppStoreAdapter",
    "GovHotlineAdapter",
    "FeedbackInboundProcessor",
    "Ingestor",
]