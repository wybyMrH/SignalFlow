"""SignalFlow 后端 - 工单系统渠道适配器（ticket_system）。

协议：REST API / Webhook，轮询 + 回调（双向）。
- fetch_raw：GET {base_url}/api/v1/tickets?status=open 轮询增量工单
- parse：工单 JSON → FeedbackEvent
- normalize：FeedbackEvent → StandardFeedback（source_ref=ticket_system:{ticket_id} 幂等键）
- update_status：PATCH 工单状态，回写处理结果（人工闭环回传）

HTTP 客户端可注入，便于测试用本地 fixture mock 外部工单系统。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.integrations.base import (
    BaseAdapter,
    FeedbackEvent,
    StandardFeedback,
    logger,
)

# 工单状态回写时允许的外部状态映射（外部系统状态码各不相同，映射保持可配置）
TICKET_STATUS_MAP: dict[str, str] = {
    "new": "open",
    "analyzing": "in_progress",
    "ai_reviewing": "in_progress",
    "ai_replied": "in_progress",
    "replied": "in_progress",
    "resolved": "resolved",
    "closed": "closed",
}


def _parse_dt(value: Any) -> datetime:
    """解析外部系统时间字段；解析失败回退当前时间。"""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            logger.warning("无法解析工单时间字段：%r", value)
    return datetime.now(timezone.utc)


class TicketSystemAdapter(BaseAdapter):
    """工单系统 REST 适配器。

    Args:
        base_url: 工单系统 API 根地址（不含 /api/v1）。
        api_token: Bearer Token，用于鉴权。
        http_client: 可选 httpx.Client（测试注入 mock 客户端）。
    """

    channel = "ticket_system"
    source = "ticket"

    def __init__(
        self,
        *,
        base_url: str,
        api_token: str | None = None,
        tenant_id: str = "default",
        http_client: httpx.Client | None = None,
    ) -> None:
        super().__init__(tenant_id=tenant_id)
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self._http = http_client or httpx.Client(timeout=10.0)

    # ──────────────────────────────────────────────
    # 拉取
    # ──────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    def fetch_raw(self, *, limit: int = 100) -> list[dict[str, Any]]:
        """轮询拉取打开状态的工单原始数据。"""
        resp = self._http.get(
            f"{self.base_url}/api/v1/tickets",
            params={"status": "open", "page_size": limit},
            headers=self._headers(),
        )
        resp.raise_for_status()
        payload = resp.json()
        # 兼容常见分页包体：{tickets:[]} / {items:[]} / {data:[]} / 裸数组
        if isinstance(payload, list):
            return payload
        for key in ("tickets", "items", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        return []

    # ──────────────────────────────────────────────
    # 解析与标准化
    # ──────────────────────────────────────────────

    def parse(self, raw: dict[str, Any]) -> FeedbackEvent:
        """将单条工单解析为统一反馈事件。"""
        if not isinstance(raw, dict):
            raise ValueError(f"工单原始数据必须是对象，实际为 {type(raw).__name__}")

        ticket_id = str(raw.get("id") or raw.get("ticket_id") or "").strip()
        if not ticket_id:
            raise ValueError("工单缺少 id/ticket_id 字段")

        content = (
            raw.get("description")
            or raw.get("content")
            or raw.get("body")
            or ""
        ).strip()
        if not content:
            raise ValueError(f"工单 {ticket_id} 缺少描述内容")

        customer = raw.get("customer") if isinstance(raw.get("customer"), dict) else {}
        customer_id = (
            customer.get("id")
            or customer.get("email")
            or raw.get("customer_id")
            or raw.get("reporter")
            or None
        )
        subject = raw.get("subject") or raw.get("title") or ""

        return FeedbackEvent(
            source=self.source,
            channel=self.channel,
            raw_content=content,
            customer_id=str(customer_id) if customer_id else None,
            timestamp=_parse_dt(raw.get("created_at") or raw.get("createdAt")),
            metadata={
                "ticket_id": ticket_id,
                "subject": subject,
                "status": raw.get("status"),
                "priority": raw.get("priority"),
                "tags": raw.get("tags") or [],
                "channel_label": "工单系统",
            },
        )

    def normalize(self, event: FeedbackEvent) -> StandardFeedback:
        """事件 → 标准反馈，source_ref 为幂等去重键。"""
        ticket_id = str(event.metadata.get("ticket_id") or "")
        return StandardFeedback(
            source=event.source,
            source_ref=f"{self.channel}:{ticket_id}" if ticket_id else None,
            content=event.raw_content,
            author=event.customer_id,
            customer_id=event.customer_id,
            channel=self.channel,
            metadata=event.metadata,
        )

    # ──────────────────────────────────────────────
    # 状态回写（双向）
    # ──────────────────────────────────────────────

    def update_status(
        self, ticket_id: str, status: str, *, reply: str | None = None
    ) -> bool:
        """将内部处理状态回写工单系统（人工审批/回复闭环）。"""
        external_status = TICKET_STATUS_MAP.get(status, status)
        payload: dict[str, Any] = {"status": external_status}
        if reply:
            payload["reply"] = reply
        resp = self._http.patch(
            f"{self.base_url}/api/v1/tickets/{ticket_id}",
            json=payload,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.status_code < 300

    def close(self) -> None:
        """释放底层 HTTP 连接（由编排层负责调用）。"""
        self._http.close()