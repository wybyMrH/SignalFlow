"""SignalFlow 后端 - 应用商店评论渠道适配器（app_store）。

协议：官方 API / 定时爬虫（单向读取）。
骨架阶段实现评论解析/标准化逻辑；fetch_raw 在未配置 API 端点时返回空列表，
配置 endpoint + app_id 后可定时拉取应用商店用户评论。
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from app.integrations.base import (
    BaseAdapter,
    FeedbackEvent,
    StandardFeedback,
    logger,
)


def _extract_version(text: str) -> str:
    """尝试从评论文本提取 App 版本号（如 1.2.3），便于按版本聚合问题。"""
    match = re.search(r"\b(\d+\.\d+(?:\.\d+)?)\b", text)
    return match.group(1) if match else ""


class AppStoreAdapter(BaseAdapter):
    """应用商店评论适配器：解析评分与评论内容。"""

    channel = "app_store"
    source = "review"

    def __init__(
        self,
        *,
        store: str = "app_store",
        app_id: str = "",
        endpoint: str | None = None,
        tenant_id: str = "default",
    ) -> None:
        super().__init__(tenant_id=tenant_id)
        self.store = store  # app_store / app_store_cn / google_play
        self.app_id = app_id
        self.endpoint = endpoint

    # ──────────────────────────────────────────────
    # 拉取（骨架：需配置评论 API/爬虫后启用）
    # ──────────────────────────────────────────────

    def fetch_raw(self, *, limit: int = 100) -> list[dict[str, Any]]:
        """定时拉取应用商店评论；未配置 endpoint 时返回空列表。

        接入真实环境时在此请求应用商店官方评论 API 或爬虫结果，
        每条评论转成统一 dict：{id, rating, title, text, author, date, app_id}
        """
        if not self.endpoint:
            logger.info("AppStore 适配器未配置评论 endpoint，跳过拉取")
            return []
        # TODO(slice): 接入官方 API / 爬虫，见 backend-integration-plan.md 阶段 5
        return []

    # ──────────────────────────────────────────────
    # 解析与标准化
    # ──────────────────────────────────────────────

    def parse(self, raw: dict[str, Any]) -> FeedbackEvent:
        """将单条应用商店评论解析为统一反馈事件。"""
        if not isinstance(raw, dict):
            raise ValueError(f"评论原始数据必须是对象，实际为 {type(raw).__name__}")

        review_id = str(raw.get("id") or raw.get("review_id") or "").strip()
        text = (
            raw.get("text")
            or raw.get("content")
            or raw.get("comment")
            or ""
        ).strip()
        title = str(raw.get("title") or "").strip()
        full_text = f"{title}：{text}" if title and text else (title or text)
        if not full_text:
            raise ValueError(f"评论 {review_id or '(无 ID)'} 缺少文本内容")

        rating = raw.get("rating")
        author = raw.get("author") or raw.get("user") or raw.get("nickname") or None
        ts_raw = raw.get("date") or raw.get("updated") or raw.get("timestamp")
        ts: datetime
        if isinstance(ts_raw, str):
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except ValueError:
                ts = datetime.now(timezone.utc)
        else:
            ts = datetime.now(timezone.utc)

        return FeedbackEvent(
            source=self.source,
            channel=self.channel,
            raw_content=full_text,
            customer_id=str(author) if author else None,
            timestamp=ts,
            metadata={
                "review_id": review_id,
                "store": self.store,
                "app_id": raw.get("app_id") or self.app_id,
                "rating": int(rating) if isinstance(rating, (int, float)) else None,
                "app_version": _extract_version(full_text),
                "channel_label": "应用商店评论",
            },
        )

    def normalize(self, event: FeedbackEvent) -> StandardFeedback:
        """事件 → 标准反馈，source_ref 以 review_id 为幂等键。"""
        review_id = str(event.metadata.get("review_id") or "")
        return StandardFeedback(
            source=event.source,
            source_ref=f"{self.channel}:{review_id}" if review_id else None,
            content=event.raw_content,
            author=event.customer_id,
            customer_id=event.customer_id,
            channel=self.channel,
            metadata=event.metadata,
        )