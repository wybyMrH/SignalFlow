"""SignalFlow 后端 - 驾驶舱统计服务。

KPI 聚合查询（今日新增 / 待处理 / 逾期 / 办结率）与轻量缓存。
统计逻辑集中在纯函数 compute_kpis，便于无数据库单元测试；
缓存通过 KeyValueCache 协议注入（生产环境可注册 Redis 同步适配器，
复用 app/core/cache.py 的 CacheClient 序列化约定）。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Protocol

from app.models.feedback import Feedback
from app.repositories.feedback import FeedbackRepository
from app.repositories.insight import InsightTopicRepository
from app.services.base import ServiceBase
from app.services.feedback import PENDING_STATUSES
from sqlalchemy.orm import Session

# 办结状态集合（办结率口径）
DONE_STATUSES: set[str] = {"resolved", "closed"}

# 驾驶舱缓存键前缀
DASHBOARD_CACHE_PREFIX = "dashboard:kpi"

# KPI 缓存默认有效期（秒）
DASHBOARD_CACHE_TTL = 60


class KeyValueCache(Protocol):
    """同步 KV 缓存抽象。

    get/set 均为同步约定；生产适配器可包装 core/cache.py 的 CacheClient
    （异步 Redis 客户端需在 API 层通过 async 桥接）。
    """

    def get(self, key: str) -> Any | None: ...
    def set(self, key: str, value: Any, *, expire_seconds: int | None = None) -> bool: ...


class DashboardService(ServiceBase):
    """驾驶舱聚合统计服务。"""

    def __init__(
        self,
        session: Session,
        *,
        feedback_repo: FeedbackRepository | None = None,
        insight_repo: InsightTopicRepository | None = None,
        cache: KeyValueCache | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(session)
        self._feedback = feedback_repo or FeedbackRepository(session)
        self._insights = insight_repo or InsightTopicRepository(session)
        self._cache = cache
        self._now = now or (lambda: datetime.now(timezone.utc))

    # ──────────────────────────────────────────────
    # KPI 纯函数
    # ──────────────────────────────────────────────

    @staticmethod
    def compute_kpis(
        feedbacks: list[Feedback],
        *,
        now: datetime,
        overdue_days: int = 7,
    ) -> dict[str, Any]:
        """由反馈列表计算驾驶舱 KPI（纯函数，便于单元测试）。

        - today_new: 今日新增反馈数
        - pending: 待处理数（new/analyzing/ai_reviewing）
        - overdue: 超过 overdue_days 天仍未办结的待处理数
        - resolved_rate: 办结率（resolved/closed 占总数百分比，保留 1 位小数）
        """
        today = now.date()
        today_new = 0
        pending = 0
        overdue = 0
        done = 0
        for f in feedbacks:
            created = f.created_at
            if created is not None and created.date() == today:
                today_new += 1
            if f.status in PENDING_STATUSES:
                pending += 1
                if created is not None and (now - created).days >= overdue_days:
                    overdue += 1
            if f.status in DONE_STATUSES:
                done += 1
        total = len(feedbacks)
        resolved_rate = round(done / total * 100, 1) if total else 0.0
        return {
            "today_new": today_new,
            "pending": pending,
            "overdue": overdue,
            "resolved": done,
            "total": total,
            "resolved_rate": resolved_rate,
        }

    # ──────────────────────────────────────────────
    # 聚合查询与缓存
    # ──────────────────────────────────────────────

    def kpi_overview(
        self,
        *,
        overdue_days: int = 7,
        cache_seconds: int | None = DASHBOARD_CACHE_TTL,
    ) -> dict[str, Any]:
        """驾驶舱 KPI 总览（今日新增 / 待办 / 逾期 / 办结率 + Top 主题）。

        优先读取缓存，未命中时计算并回写；未注入 cache 时直算不缓存。
        """
        cache_key = f"{DASHBOARD_CACHE_PREFIX}:overdue:{overdue_days}"
        if self._cache is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        feedbacks = list(self._feedback.list_all())  # type: ignore[arg-type]
        kpis = self.compute_kpis(feedbacks, now=self._now(), overdue_days=overdue_days)
        topics = sorted(
            self._insights.list_all(),  # type: ignore[arg-type]
            key=lambda t: t.priority_score or 0,
            reverse=True,
        )
        kpis["top_topics"] = [t.title for t in topics[:5]]

        if self._cache is not None:
            self._cache.set(cache_key, kpis, expire_seconds=cache_seconds)
        return kpis