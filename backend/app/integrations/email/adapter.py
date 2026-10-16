"""SignalFlow 后端 - 邮件渠道适配器（email）。

协议：IMAP / SMTP 轮询收件箱（单向读取 + 回复发送）。
骨架阶段实现解析/标准化逻辑；fetch_raw 在未配置 IMAP 时返回空列表，
配置 host/user/password 后可轮询收件箱中的客户反馈邮件。
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


def _parse_mail_date(value: Any) -> datetime:
    """解析邮件 Date 头字段（RFC 2822 / ISO）；失败回退当前时间。"""
    if not value:
        return datetime.now(timezone.utc)
    try:
        from email.utils import parsedate_to_datetime

        dt = parsedate_to_datetime(value)
        if dt is None:
            raise ValueError
        return dt
    except (ValueError, TypeError):
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            logger.warning("无法解析邮件时间字段：%r", value)
            return datetime.now(timezone.utc)


# 可配置的来源白名单：仅收集这些发件域的邮件，防止误收订阅/通知
ALLOWED_FROM_DOMAINS: tuple[str, ...] = ("customer.example.com", "mail.example.com")


class EmailAdapter(BaseAdapter):
    """邮件轮询适配器：解析客户来信为反馈事件。"""

    channel = "email"
    source = "email"

    def __init__(
        self,
        *,
        imap_host: str | None = None,
        imap_user: str | None = None,
        imap_password: str | None = None,
        mailbox: str = "INBOX",
        tenant_id: str = "default",
        allowed_from_domains: tuple[str, ...] = ALLOWED_FROM_DOMAINS,
    ) -> None:
        super().__init__(tenant_id=tenant_id)
        self._imap_host = imap_host
        self._imap_user = imap_user
        self._imap_password = imap_password
        self._mailbox = mailbox
        self._allowed_from_domains = allowed_from_domains

    # ──────────────────────────────────────────────
    # 拉取（骨架：需配置 IMAP 后启用）
    # ──────────────────────────────────────────────

    def fetch_raw(self, *, limit: int = 100) -> list[dict[str, Any]]:
        """轮询收件箱未读邮件；未配置 IMAP 时返回空列表。

        接入真实环境时在此连接 imaplib，拉取未读邮件并转成统一 dict：
        {message_id, from_, from_name, to, subject, body, date}
        """
        if not (self._imap_host and self._imap_user):
            logger.info("Email 适配器未配置 IMAP（host=%r user=%r），跳过拉取", self._imap_host, self._imap_user)
            return []
        # TODO(slice): 接入 imaplib 轮询逻辑，见 backend-integration-plan.md 阶段 5
        return []

    # ──────────────────────────────────────────────
    # 解析与标准化
    # ──────────────────────────────────────────────

    def parse(self, raw: dict[str, Any]) -> FeedbackEvent:
        """将单封邮件解析为统一反馈事件。"""
        if not isinstance(raw, dict):
            raise ValueError(f"邮件原始数据必须是对象，实际为 {type(raw).__name__}")

        message_id = str(raw.get("message_id") or raw.get("Message-ID") or "").strip()
        body = (
            raw.get("body")
            or raw.get("text")
            or raw.get("content")
            or ""
        ).strip()
        if not body:
            raise ValueError(f"邮件 {message_id or '(无 ID)'} 缺少正文")

        sender = str(raw.get("from_") or raw.get("from") or "").strip()
        sender_name = str(raw.get("from_name") or "").strip()

        return FeedbackEvent(
            source=self.source,
            channel=self.channel,
            raw_content=body,
            customer_id=sender or None,
            timestamp=_parse_mail_date(raw.get("date") or raw.get("Date")),
            metadata={
                "message_id": message_id,
                "from": sender,
                "from_name": sender_name,
                "to": raw.get("to"),
                "subject": raw.get("subject") or "",
                "channel_label": "邮件",
            },
        )

    def normalize(self, event: FeedbackEvent) -> StandardFeedback:
        """事件 → 标准反馈，source_ref 以 Message-ID 为幂等键。"""
        message_id = str(event.metadata.get("message_id") or "")
        return StandardFeedback(
            source=event.source,
            source_ref=f"{self.channel}:{message_id}" if message_id else None,
            content=event.raw_content,
            author=event.customer_id,
            customer_id=event.customer_id,
            channel=self.channel,
            metadata=event.metadata,
        )