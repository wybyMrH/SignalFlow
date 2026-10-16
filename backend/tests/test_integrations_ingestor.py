"""SignalFlow 后端 - 入站处理器与渠道编排器测试（阶段 5 验收标准 ②）。

覆盖：
- FeedbackInboundProcessor 落库与 source_ref 幂等去重；
- Ingestor.run_once 全渠道消费；
- 单渠道拉取失败 / 单条处理失败被隔离，不影响其他渠道与主服务。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.integrations.base import (
    BaseAdapter,
    ChannelRegistry,
    FeedbackEvent,
    StandardFeedback,
)
from app.integrations.processor import FeedbackInboundProcessor, Ingestor
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate
from tests.mocks import FakeSession, MemoryRepo


class FakeFeedbackRepo(MemoryRepo):
    """内存版反馈仓储：支持 source_ref 幂等查询与 FeedbackCreate 落库。"""

    def get_by_source_ref(
        self, source_ref: str, *, tenant_id: str = "default"
    ) -> Feedback | None:
        for item in self._items:
            if getattr(item, "source_ref", None) == source_ref and item.tenant_id == tenant_id:
                return item
        return None

    def add(self, data: FeedbackCreate, tenant_id: str = "default") -> Feedback:
        now = datetime.now(timezone.utc)
        feedback = Feedback(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            source=data.source,
            source_ref=data.source_ref,
            content=data.content,
            author=data.author,
            status="new",
            created_at=now,
            updated_at=now,
        )
        return self.create(feedback)


def make_processor() -> tuple[FeedbackInboundProcessor, FakeFeedbackRepo, FakeSession]:
    repo = FakeFeedbackRepo()
    session = FakeSession()
    return FeedbackInboundProcessor(repo, session), repo, session


class TestFeedbackInboundProcessor:
    def test_process_ingests_and_commits(self) -> None:
        processor, repo, session = make_processor()
        std = StandardFeedback(
            source="ticket",
            source_ref="ticket_system:1",
            content="测试内容",
            author="客户A",
            channel="ticket_system",
        )

        feedback_id = processor.process(std, tenant_id="default")

        assert feedback_id
        assert session.commits == 1
        persisted = repo.list_all()[0]
        assert persisted.source_ref == "ticket_system:1"
        assert persisted.content == "测试内容"
        assert persisted.author == "客户A"
        assert persisted.status == "new"
        assert persisted.tenant_id == "default"

    def test_process_skips_duplicate_source_ref(self) -> None:
        processor, repo, session = make_processor()
        std = StandardFeedback(
            source="ticket",
            source_ref="ticket_system:1",
            content="测试内容",
            channel="ticket_system",
        )

        first_id = processor.process(std, tenant_id="default")
        second_id = processor.process(std, tenant_id="default")

        assert first_id == second_id
        assert len(repo.list_all()) == 1
        assert session.commits == 1

    def test_process_allows_repeat_without_source_ref(self) -> None:
        """无 source_ref（如手动录入）不参与去重，允许重复入库。"""
        processor, repo, session = make_processor()
        std = StandardFeedback(
            source="manual",
            source_ref=None,
            content="手动录入",
            channel="base",
        )

        processor.process(std, tenant_id="default")
        processor.process(std, tenant_id="default")

        assert len(repo.list_all()) == 2
        assert session.commits == 2


class _FakeChannelAdapter(BaseAdapter):
    """测试用适配器：直接消费预置事件列表；可模拟拉取失败。"""

    channel = "fake"
    source = "fake"

    def __init__(
        self,
        channel: str,
        events: list[FeedbackEvent] | None = None,
        *,
        raise_on_fetch: bool = False,
    ) -> None:
        super().__init__()
        self.channel = channel
        self.source = channel
        self._events = list(events or [])
        self._raise_on_fetch = raise_on_fetch

    def fetch_raw(self, *, limit: int = 100) -> list[object]:
        if self._raise_on_fetch:
            raise RuntimeError("upstream unavailable")
        return list(self._events)

    def parse(self, raw: object) -> FeedbackEvent:
        return raw  # type: ignore[return-value]

    def normalize(self, event: FeedbackEvent) -> StandardFeedback:
        return StandardFeedback(
            source=event.source,
            source_ref=f"{self.channel}:{event.metadata.get('seq')}",
            content=event.raw_content,
            channel=self.channel,
        )


def make_event(seq: int, content: str = "反馈内容") -> FeedbackEvent:
    return FeedbackEvent(
        source="fake",
        channel="fake",
        raw_content=content,
        metadata={"seq": seq},
    )


class TestIngestor:
    def test_run_once_consumes_all_channels(self) -> None:
        processor, repo, _session = make_processor()
        registry = ChannelRegistry()
        registry.register(
            _FakeChannelAdapter("email", [make_event(1, "邮件反馈"), make_event(2, "邮件反馈2")])
        )
        registry.register(
            _FakeChannelAdapter("app_store", [make_event(1, "评论反馈")])
        )
        ingestor = Ingestor(processor, registry=registry)

        stats = ingestor.run_once(tenant_id="default")

        assert stats["email"] == {"fetched": 2, "processed": 2, "errors": 0}
        assert stats["app_store"] == {"fetched": 1, "processed": 1, "errors": 0}
        assert len(repo.list_all()) == 3

    def test_fetch_failure_is_isolated(self) -> None:
        """验收标准 ②：单渠道拉取失败不影响其他渠道与主服务。"""
        processor, repo, _session = make_processor()
        registry = ChannelRegistry()
        registry.register(_FakeChannelAdapter("email", [make_event(1)], raise_on_fetch=True))
        registry.register(_FakeChannelAdapter("app_store", [make_event(1)]))
        ingestor = Ingestor(processor, registry=registry)

        stats = ingestor.run_once(tenant_id="default")  # 不抛异常

        assert stats["email"]["fetched"] == 0
        assert stats["email"]["errors"] >= 1
        assert stats["app_store"]["processed"] == 1
        assert len(repo.list_all()) == 1  # 正常渠道照常入库

    def test_item_failure_is_isolated(self) -> None:
        """单条标准反馈处理失败只计错误，不影响同渠道其他条。"""
        processor, repo, session = make_processor()
        failing_processor = _RaisingProcessor(processor, bad_content="坏数据")
        registry = ChannelRegistry()
        registry.register(
            _FakeChannelAdapter(
                "email",
                [make_event(1, "正常内容"), make_event(2, "坏数据")],
            )
        )
        ingestor = Ingestor(failing_processor, registry=registry)

        stats = ingestor.run_once(tenant_id="default")

        assert stats["email"]["fetched"] == 2
        assert stats["email"]["processed"] == 1
        assert stats["email"]["errors"] == 1
        assert len(repo.list_all()) == 1
        assert session.commits == 1


class _RaisingProcessor:
    """包装真实 processor：遇到特定内容时抛异常，用于验证失败隔离。"""

    def __init__(self, inner: FeedbackInboundProcessor, *, bad_content: str) -> None:
        self._inner = inner
        self._bad_content = bad_content

    def process(self, feedback: StandardFeedback, *, tenant_id: str = "default") -> str:
        if self._bad_content in feedback.content:
            raise RuntimeError("processing failed")
        return self._inner.process(feedback, tenant_id=tenant_id)