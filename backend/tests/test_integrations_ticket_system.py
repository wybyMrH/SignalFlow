"""SignalFlow 后端 - 工单系统适配器测试（阶段 5 验收标准 ①）。

覆盖端到端链路：外部 API mock → fetch_raw → parse → normalize → 入库，
以及 fetch_raw 响应结构兼容、状态回写映射与 source_ref 幂等去重。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import httpx
import pytest

from app.integrations.base import FeedbackEvent, StandardFeedback
from app.integrations.processor import FeedbackInboundProcessor
from app.integrations.ticket_system import TicketSystemAdapter
from app.integrations.ticket_system.adapter import TICKET_STATUS_MAP
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate
from tests.mocks import FakeSession, MemoryRepo

BASE_URL = "https://ticket.example.com"
API_TOKEN = "secret-token"

SAMPLE_TICKET = {
    "id": 12345,
    "subject": "无法登录系统",
    "description": "登录时一直提示密码错误，重置密码也不行",
    "status": "open",
    "priority": "high",
    "tags": ["login", "account"],
    "customer": {"id": "cust-9", "email": "a@example.com"},
    "created_at": "2026-10-14T09:30:00+00:00",
}


def make_client(handler: httpx.MockTransport.Handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def make_adapter(handler: httpx.MockTransport.Handler) -> TicketSystemAdapter:
    return TicketSystemAdapter(
        base_url=BASE_URL,
        api_token=API_TOKEN,
        http_client=make_client(handler),
    )


class TestFetchRaw:
    @pytest.mark.parametrize(
        ("payload_key", "payload"),
        [
            ("tickets", {"tickets": [SAMPLE_TICKET]}),
            ("items", {"items": [SAMPLE_TICKET]}),
            ("data", {"data": [SAMPLE_TICKET]}),
            ("bare", [SAMPLE_TICKET]),
        ],
    )
    def test_returns_ticket_list_from_common_shapes(
        self, payload_key: str, payload: object
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=payload)

        adapter = make_adapter(handler)
        raw = adapter.fetch_raw()
        assert raw == [SAMPLE_TICKET]

    def test_returns_empty_on_unknown_shape(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"foo": "bar"})

        adapter = make_adapter(handler)
        assert adapter.fetch_raw() == []

    def test_sends_auth_and_query_params(self) -> None:
        captured: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["auth"] = request.headers.get("Authorization")
            return httpx.Response(200, json={"items": []})

        adapter = make_adapter(handler)
        adapter.fetch_raw(limit=50)

        assert captured["auth"] == f"Bearer {API_TOKEN}"
        assert "status=open" in str(captured["url"])
        assert "page_size=50" in str(captured["url"])
        assert "/api/v1/tickets" in str(captured["url"])


class TestParse:
    def test_parse_full_ticket(self) -> None:
        adapter = make_adapter(lambda request: httpx.Response(200, json=[]))
        event = adapter.parse(SAMPLE_TICKET)

        assert isinstance(event, FeedbackEvent)
        assert event.source == "ticket"
        assert event.channel == "ticket_system"
        assert event.raw_content == SAMPLE_TICKET["description"]
        assert event.customer_id == "cust-9"
        assert event.timestamp == datetime(2026, 10, 14, 9, 30, tzinfo=timezone.utc)
        assert event.metadata["ticket_id"] == "12345"
        assert event.metadata["subject"] == "无法登录系统"
        assert event.metadata["status"] == "open"
        assert event.metadata["channel_label"] == "工单系统"

    def test_parse_supports_ticket_id_and_created_at(self) -> None:
        adapter = make_adapter(lambda request: httpx.Response(200, json=[]))
        raw = {
            "ticket_id": 67890,
            "title": "咨询",
            "content": "企业认证需要哪些材料？",
            "reporter": "rep-1",
            "createdAt": "2026-10-14T10:00:00Z",
        }
        event = adapter.parse(raw)
        assert event.metadata["ticket_id"] == "67890"
        assert event.metadata["subject"] == "咨询"
        assert event.customer_id == "rep-1"
        assert event.timestamp == datetime(2026, 10, 14, 10, 0, tzinfo=timezone.utc)

    def test_parse_missing_id_raises(self) -> None:
        adapter = make_adapter(lambda request: httpx.Response(200, json=[]))
        with pytest.raises(ValueError, match="id/ticket_id"):
            adapter.parse({"description": "无编号的工单"})

    def test_parse_missing_content_raises(self) -> None:
        adapter = make_adapter(lambda request: httpx.Response(200, json=[]))
        with pytest.raises(ValueError, match="缺少描述内容"):
            adapter.parse({"id": 1, "subject": "空内容"})

    def test_parse_non_dict_raises(self) -> None:
        adapter = make_adapter(lambda request: httpx.Response(200, json=[]))
        with pytest.raises(ValueError, match="必须是对象"):
            adapter.parse(["not-a-dict"])  # type: ignore[arg-type]


class TestNormalize:
    def test_normalize_sets_source_ref_and_content(self) -> None:
        adapter = make_adapter(lambda request: httpx.Response(200, json=[]))
        event = adapter.parse(SAMPLE_TICKET)
        std = adapter.normalize(event)

        assert isinstance(std, StandardFeedback)
        assert std.source_ref == "ticket_system:12345"
        assert std.content == SAMPLE_TICKET["description"]
        assert std.author == "cust-9"
        assert std.customer_id == "cust-9"
        assert std.channel == "ticket_system"


class TestFetchNew:
    def test_full_pipeline_returns_standard_feedback(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"items": [SAMPLE_TICKET]})

        adapter = make_adapter(handler)
        items = adapter.fetch_new()

        assert len(items) == 1
        assert isinstance(items[0], StandardFeedback)
        assert items[0].source_ref == "ticket_system:12345"
        assert "密码错误" in items[0].content


class TestUpdateStatus:
    @pytest.mark.parametrize(
        ("internal_status", "expected_external"),
        [
            ("new", "open"),
            ("analyzing", "in_progress"),
            ("ai_reviewing", "in_progress"),
            ("ai_replied", "in_progress"),
            ("replied", "in_progress"),
            ("resolved", "resolved"),
            ("closed", "closed"),
        ],
    )
    def test_status_mapping(
        self, internal_status: str, expected_external: str
    ) -> None:
        captured: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["json"] = request.content
            return httpx.Response(200, json={"ok": True})

        adapter = make_adapter(handler)
        assert adapter.update_status("12345", internal_status) is True

        assert f"/api/v1/tickets/12345" in str(captured["url"])
        assert TICKET_STATUS_MAP[internal_status] == expected_external
        # request.content 是 UTF-8 JSON，重新解析验证 payload
        import json

        body = json.loads(captured["json"])  # type: ignore[arg-type]
        assert body["status"] == expected_external

    def test_update_with_reply(self) -> None:
        captured: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["json"] = request.content
            return httpx.Response(204)

        adapter = make_adapter(handler)
        assert adapter.update_status("1", "replied", reply="已受理，正在处理") is True

        import json

        body = json.loads(captured["json"])  # type: ignore[arg-type]
        assert body["status"] == "in_progress"
        assert body["reply"] == "已受理，正在处理"

    def test_unmapped_status_passthrough(self) -> None:
        captured: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["json"] = request.content
            return httpx.Response(200, json={"ok": True})

        adapter = make_adapter(handler)
        adapter.update_status("3", "custom_state")

        import json

        body = json.loads(captured["json"])  # type: ignore[arg-type]
        assert body["status"] == "custom_state"


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


class TestEndToEndIngest:
    def test_process_ingests_standard_feedback_and_commits(self) -> None:
        repo = FakeFeedbackRepo()
        session = FakeSession()
        processor = FeedbackInboundProcessor(repo, session)

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"items": [SAMPLE_TICKET]})

        adapter = make_adapter(handler)
        [std] = adapter.fetch_new()

        feedback_id = processor.process(std, tenant_id="default")

        assert isinstance(feedback_id, str)
        assert len(repo.list_all()) == 1
        assert session.commits == 1
        persisted = repo.list_all()[0]
        assert persisted.source_ref == "ticket_system:12345"
        assert persisted.source == "ticket"
        assert "密码错误" in persisted.content
        assert persisted.status == "new"

    def test_process_dedupes_by_source_ref(self) -> None:
        repo = FakeFeedbackRepo()
        session = FakeSession()
        processor = FeedbackInboundProcessor(repo, session)

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"items": [SAMPLE_TICKET]})

        adapter = make_adapter(handler)
        [std] = adapter.fetch_new()

        first_id = processor.process(std, tenant_id="default")
        second_id = processor.process(std, tenant_id="default")

        assert first_id == second_id  # 幂等：同一条外部工单返回同一反馈 id
        assert len(repo.list_all()) == 1
        assert session.commits == 1  # 仅首次落库提交

    def test_full_pipeline_two_tickets_to_db(self) -> None:
        ticket2 = {**SAMPLE_TICKET, "id": 12346, "description": "导出报表一直转圈"}
        repo = FakeFeedbackRepo()
        session = FakeSession()
        processor = FeedbackInboundProcessor(repo, session)

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"items": [SAMPLE_TICKET, ticket2]})

        adapter = make_adapter(handler)
        items = adapter.fetch_new()

        for std in items:
            processor.process(std, tenant_id="default")

        assert len(repo.list_all()) == 2
        refs = {it.source_ref for it in repo.list_all()}
        assert refs == {"ticket_system:12345", "ticket_system:12346"}