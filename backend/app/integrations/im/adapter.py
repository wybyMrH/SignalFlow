"""SignalFlow 后端 - 企业微信 IM 渠道适配器（im）。

协议：Webhook / Bot API（被动接收）。
IM 渠道由外部系统主动推送，适配器不轮询；业务侧收到 Webhook 后调用
parse_webhook(payload) 即可把消息体解析为标准反馈事件。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.integrations.base import (
    BaseAdapter,
    FeedbackEvent,
    StandardFeedback,
    logger,
)


class IMAdapter(BaseAdapter):
    """企业微信/IM Bot 适配器：解析被动推送消息。"""

    channel = "im"
    source = "im"

    def __init__(self, *, tenant_id: str = "default") -> None:
        super().__init__(tenant_id=tenant_id)

    # ──────────────────────────────────────────────
    # 拉取（被动接收渠道：不轮询）
    # ──────────────────────────────────────────────

    def fetch_raw(self, *, limit: int = 100) -> list[Any]:
        """IM 渠道为被动接收，无主动拉取源，返回空列表。"""
        return []

    # ──────────────────────────────────────────────
    # 解析与标准化
    # ──────────────────────────────────────────────

    def parse(self, raw: dict[str, Any]) -> FeedbackEvent:
        """将 IM 消息 dict 解析为统一反馈事件。"""
        if not isinstance(raw, dict):
            raise ValueError(f"IM 消息原始数据必须是对象，实际为 {type(raw).__name__}")

        msg_id = str(raw.get("msg_id") or raw.get("MsgId") or raw.get("id") or "").strip()
        content = str(raw.get("content") or raw.get("Content") or "").strip()
        if not content:
            raise ValueError(f"IM 消息 {msg_id or '(无 ID)'} 缺少内容")

        sender = (
            raw.get("from_user")
            or raw.get("FromUser")
            or raw.get("sender")
            or raw.get("from")
            or None
        )
        ts_raw = raw.get("create_time") or raw.get("CreateTime") or raw.get("timestamp")
        ts: datetime
        if isinstance(ts_raw, (int, float)) and ts_raw > 0:
            ts = datetime.fromtimestamp(ts_raw, tz=timezone.utc)
        elif isinstance(ts_raw, str):
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except ValueError:
                ts = datetime.now(timezone.utc)
        else:
            ts = datetime.now(timezone.utc)

        return FeedbackEvent(
            source=self.source,
            channel=self.channel,
            raw_content=content,
            customer_id=str(sender) if sender else None,
            timestamp=ts,
            metadata={
                "msg_id": msg_id,
                "sender": sender,
                "msg_type": raw.get("msg_type") or raw.get("MsgType") or "text",
                "channel_label": "企业微信",
            },
        )

    def parse_webhook(self, payload: dict[str, Any]) -> FeedbackEvent:
        """企业微信回调通用包体解析：剥离外层 envelope 后委托 parse。"""
        if not isinstance(payload, dict):
            raise ValueError(f"Webhook 包体必须是对象，实际为 {type(payload).__name__}")
        inner = (
            payload.get("message")
            or payload.get("data")
            or payload.get("Event")
            or payload
        )
        return self.parse(inner if isinstance(inner, dict) else payload)

    def normalize(self, event: FeedbackEvent) -> StandardFeedback:
        """事件 → 标准反馈，source_ref 以 msg_id 为幂等键。"""
        msg_id = str(event.metadata.get("msg_id") or "")
        return StandardFeedback(
            source=event.source,
            source_ref=f"{self.channel}:{msg_id}" if msg_id else None,
            content=event.raw_content,
            author=event.customer_id,
            customer_id=event.customer_id,
            channel=self.channel,
            metadata=event.metadata,
        )