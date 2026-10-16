"""SignalFlow 后端 - 入站处理器与渠道编排器。

职责划分（阶段 5 验收标准）：
- 入站处理器（FeedbackInboundProcessor）：消费适配器产出的 StandardFeedback 并落库，
  按 source_ref 幂等去重；重复外部记录直接返回已存在 id。
- 渠道编排器（Ingestor）：遍历注册的适配器，逐渠道隔离异常——
  单渠道拉取/处理失败仅记入独立日志通道（signalflow.integrations），
  不影响其他渠道与主服务（验收标准 ②）。

设计约束：适配器层不直接写数据库；本模块是唯一允许落库的入口。
"""

from __future__ import annotations

from typing import Any

from app.integrations.base import (
    ChannelRegistry,
    StandardFeedback,
    channel_registry,
    logger,
)
from app.repositories.feedback import FeedbackRepository
from app.schemas.feedback import FeedbackCreate


class FeedbackInboundProcessor:
    """按 source_ref 幂等消费标准反馈并落库的入站处理器。

    Args:
        repo: 反馈仓储（真实环境为 FeedbackRepository；测试可注入内存 fake）。
        session: 事务边界（SQLAlchemy Session）；每成功处理一条提交一次。
    """

    def __init__(self, repo: FeedbackRepository, session: Any) -> None:
        self._repo = repo
        self._session = session

    def process(
        self, feedback: StandardFeedback, *, tenant_id: str = "default"
    ) -> str:
        """消费一条标准反馈并落库；重复 source_ref 幂等返回已存在 id。

        Returns:
            反馈记录 id（新建或已存在）。
        """
        source_ref = feedback.source_ref
        if source_ref:
            existing = self._repo.get_by_source_ref(source_ref, tenant_id=tenant_id)
            if existing is not None:
                logger.info(
                    "入站跳过重复反馈 source_ref=%s（已存在 id=%s）",
                    source_ref,
                    existing.id,
                )
                return str(existing.id)

        created = self._repo.add(
            FeedbackCreate(
                source=feedback.source,
                source_ref=source_ref,
                content=feedback.content,
                author=feedback.author,
            ),
            tenant_id=tenant_id,
        )
        self._session.commit()
        logger.info("入站落库反馈 id=%s source_ref=%s", created.id, source_ref)
        return str(created.id)


class Ingestor:
    """渠道编排器：遍历注册的适配器，隔离异常后统一入站落库。

    单渠道失败不影响其他渠道；每轮返回各渠道统计供监控/日志使用。
    """

    def __init__(
        self,
        processor: FeedbackInboundProcessor,
        *,
        registry: ChannelRegistry | None = None,
    ) -> None:
        self._processor = processor
        self._registry = registry or channel_registry

    def run_once(
        self, *, tenant_id: str = "default", limit: int = 100
    ) -> dict[str, dict[str, int]]:
        """执行一轮拉取 → 解析 → 标准化 → 入库，返回各渠道统计。

        Returns:
            {channel: {"fetched": 拉取条数, "processed": 消费条数, "errors": 失败条数}}
        """
        stats: dict[str, dict[str, int]] = {}
        for adapter in self._registry.all_adapters():
            per_channel = {"fetched": 0, "processed": 0, "errors": 0}
            try:
                std_items = adapter.fetch_new(limit=limit)
                per_channel["fetched"] = len(std_items)
                for item in std_items:
                    try:
                        self._processor.process(item, tenant_id=tenant_id)
                        per_channel["processed"] += 1
                    except Exception:
                        per_channel["errors"] += 1
                        logger.exception(
                            "渠道 %s 处理标准反馈失败（source_ref=%s）",
                            adapter.channel,
                            item.source_ref,
                        )
            except Exception:
                per_channel["errors"] += 1
                logger.exception("渠道 %s 拉取失败，已隔离", adapter.channel)
            stats[adapter.channel] = per_channel
        return stats