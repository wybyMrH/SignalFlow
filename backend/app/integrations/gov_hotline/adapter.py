"""SignalFlow 后端 - 政务 12345 热线渠道适配器（gov_hotline）。

协议：Kafka / 文件交换 / 数据库视图（实时流 / 定时同步，单向读取 + 结果回写）。
骨架阶段实现热线工单解析/标准化逻辑；fetch_raw 在未配置数据源时返回空列表。
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


class GovHotlineAdapter(BaseAdapter):
    """政务热线适配器：解析诉求工单为反馈事件。"""

    channel = "gov_hotline"
    source = "hotline"

    def __init__(
        self,
        *,
        data_source: str | None = None,  # kafka_topic / file_path / db_view
        tenant_id: str = "default",
    ) -> None:
        super().__init__(tenant_id=tenant_id)
        self.data_source = data_source

    # ──────────────────────────────────────────────
    # 拉取（骨架：需配置 Kafka/文件/DB 视图后启用）
    # ──────────────────────────────────────────────

    def fetch_raw(self, *, limit: int = 100) -> list[dict[str, Any]]:
        """定时/流式同步热线工单；未配置数据源时返回空列表。

        接入真实环境时在此连接 Kafka topic（实时流）或读取交换文件 /
        数据库视图（定时同步），每行转成统一 dict：
        {id, complaint, category, citizen, accept_time, district}
        """
        if not self.data_source:
            logger.info("GovHotline 适配器未配置 data_source，跳过拉取")
            return []
        # TODO(slice): 接入 Kafka/文件/DB 视图，见 backend-integration-plan.md 阶段 5
        return []

    # ──────────────────────────────────────────────
    # 解析与标准化
    # ──────────────────────────────────────────────

    def parse(self, raw: dict[str, Any]) -> FeedbackEvent:
        """将单条热线工单解析为统一反馈事件。"""
        if not isinstance(raw, dict):
            raise ValueError(f"热线工单原始数据必须是对象，实际为 {type(raw).__name__}")

        record_id = str(
            raw.get("id")
            or raw.get("case_no")
            or raw.get("record_id")
            or raw.get("工单编号")
            or ""
        ).strip()
        content = (
            raw.get("complaint")
            or raw.get("诉求内容")
            or raw.get("content")
            or raw.get("description")
            or ""
        ).strip()
        if not content:
            raise ValueError(f"热线工单 {record_id or '(无编号)'} 缺少诉求内容")

        citizen = (
            raw.get("citizen")
            or raw.get("contact")
            or raw.get("市民")
            or raw.get("phone")
            or None
        )
        category = raw.get("category") or raw.get("事项分类") or ""

        return FeedbackEvent(
            source=self.source,
            channel=self.channel,
            raw_content=content,
            customer_id=str(citizen) if citizen else None,
            timestamp=datetime.now(timezone.utc),
            metadata={
                "record_id": record_id,
                "category": category,
                "district": raw.get("district") or raw.get("所属区县"),
                "urgency": raw.get("urgency") or raw.get("紧急程度"),
                "channel_label": "政务热线",
            },
        )

    def normalize(self, event: FeedbackEvent) -> StandardFeedback:
        """事件 → 标准反馈，source_ref 以 record_id 为幂等键。"""
        record_id = str(event.metadata.get("record_id") or "")
        return StandardFeedback(
            source=event.source,
            source_ref=f"{self.channel}:{record_id}" if record_id else None,
            content=event.raw_content,
            author=event.customer_id,
            customer_id=event.customer_id,
            channel=self.channel,
            metadata=event.metadata,
        )