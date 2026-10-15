"""SignalFlow 后端 - DashboardService 单元测试。

覆盖 KPI 纯函数（今日新增 / 待办 / 逾期 / 办结率）与缓存读回写逻辑。
使用内存 mock，不依赖数据库。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from app.models.feedback import Feedback
from app.models.insight import InsightTopic
from app.services.dashboard import DASHBOARD_CACHE_TTL, DashboardService
from tests.mocks import FakeSession, MemoryRepo


def make_feedback(
    *,
    status: str = "new",
    created_at: datetime | None = None,
) -> Feedback:
    return Feedback(
        id=uuid.uuid4(),
        tenant_id="default",
        source="hotline",
        content="测试反馈",
        author="客户A",
        status=status,
        created_at=created_at or datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def make_topic(title: str, priority: int) -> InsightTopic:
    return InsightTopic(
        id=str(uuid.uuid4()),
        title=title,
        priority_score=priority,
        strength=priority,
        feedback_count=0,
        customer_count=0,
        trend="up",
    )


class FakeCache:
    """KeyValueCache 协议的内存实现，记录 get/set 调用。"""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self.get_keys: list[str] = []
        self.set_keys: list[str] = []

    def get(self, key: str) -> Any | None:
        self.get_keys.append(key)
        return self._store.get(key)

    def set(self, key: str, value: Any, *, expire_seconds: int | None = None) -> bool:
        self.set_keys.append(key)
        self._store[key] = value
        return True


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


NOW = datetime(2026, 10, 15, 10, 0, 0, tzinfo=timezone.utc)


class TestComputeKpis:
    def test_empty_feedbacks(self) -> None:
        kpis = DashboardService.compute_kpis([], now=NOW)
        assert kpis["today_new"] == 0
        assert kpis["pending"] == 0
        assert kpis["overdue"] == 0
        assert kpis["resolved"] == 0
        assert kpis["resolved_rate"] == 0.0

    def test_kpi_aggregation(self) -> None:
        feedbacks = [
            make_feedback(status="new", created_at=NOW - timedelta(days=10)),  # 逾期待办
            make_feedback(status="new", created_at=NOW - timedelta(days=1)),  # 待办未逾期
            make_feedback(status="analyzing", created_at=NOW),  # 今日新增待办
            make_feedback(status="resolved", created_at=NOW - timedelta(days=3)),  # 已办结
            make_feedback(status="closed", created_at=NOW - timedelta(days=2)),  # 已办结
        ]
        kpis = DashboardService.compute_kpis(feedbacks, now=NOW)
        assert kpis["today_new"] == 1
        assert kpis["pending"] == 3
        assert kpis["overdue"] == 1
        assert kpis["resolved"] == 2
        assert kpis["total"] == 5
        assert kpis["resolved_rate"] == 40.0  # 2/5

    def test_overdue_threshold_custom(self) -> None:
        feedbacks = [make_feedback(status="new", created_at=NOW - timedelta(days=3))]
        kpis = DashboardService.compute_kpis(feedbacks, now=NOW, overdue_days=2)
        assert kpis["overdue"] == 1
        kpis = DashboardService.compute_kpis(feedbacks, now=NOW, overdue_days=5)
        assert kpis["overdue"] == 0


class TestKpiOverview:
    def test_without_cache_computes_directly(self, session: FakeSession) -> None:
        feedback_repo = MemoryRepo(
            [make_feedback(status="new", created_at=NOW - timedelta(days=9))]
        )
        insight_repo = MemoryRepo(
            [make_topic("窗口排队", 90), make_topic("材料复用", 60), make_topic("低频主题", 20)]
        )
        service = DashboardService(
            session,
            feedback_repo=feedback_repo,  # type: ignore[arg-type]
            insight_repo=insight_repo,  # type: ignore[arg-type]
            cache=None,
            now=lambda: NOW,
        )

        kpis = service.kpi_overview()

        assert kpis["today_new"] == 0
        assert kpis["pending"] == 1
        assert kpis["overdue"] == 1
        # Top 主题按优先级降序取前 5
        assert kpis["top_topics"] == ["窗口排队", "材料复用", "低频主题"]

    def test_cache_miss_writes_back(self, session: FakeSession) -> None:
        cache = FakeCache()
        service = DashboardService(
            session,
            feedback_repo=MemoryRepo(),  # type: ignore[arg-type]
            insight_repo=MemoryRepo([make_topic("主题A", 80)]),  # type: ignore[arg-type]
            cache=cache,
            now=lambda: NOW,
        )

        kpis = service.kpi_overview(cache_seconds=DASHBOARD_CACHE_TTL)

        assert cache.set_keys == [f"dashboard:kpi:overdue:{7}"]
        assert kpis["top_topics"] == ["主题A"]

    def test_cache_hit_skips_recompute(self, session: FakeSession) -> None:
        cache = FakeCache()
        # 预置缓存，repo 无数据也应直接返回缓存结果
        cache._store["dashboard:kpi:overdue:7"] = {
            "today_new": 42,
            "pending": 42,
            "overdue": 0,
            "resolved": 0,
            "total": 42,
            "resolved_rate": 0.0,
        }
        service = DashboardService(
            session,
            feedback_repo=MemoryRepo(),  # type: ignore[arg-type]
            insight_repo=MemoryRepo(),  # type: ignore[arg-type]
            cache=cache,
            now=lambda: NOW,
        )

        kpis = service.kpi_overview()

        assert kpis["today_new"] == 42
        assert "top_topics" not in kpis  # 缓存命中，不再合并 top_topics
        assert len(cache.get_keys) == 1