"""SignalFlow 后端 - FeedbackService 单元测试。

使用内存 mock（FakeSession + MemoryRepo），不依赖数据库。
覆盖：创建、查询过滤、状态机流转、批量流转回滚、统计。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.core.pagination import PageParams
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate
from app.services.feedback import PENDING_STATUSES, FeedbackService
from tests.mocks import FakeSession, MemoryRepo


class FakeFeedbackRepo(MemoryRepo):
    """FeedbackRepository 的 mock：add(FeedbackCreate) → Feedback ORM。"""

    def add(self, data: FeedbackCreate, tenant_id: str = "default") -> Feedback:
        feedback = Feedback(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            source=data.source,
            source_ref=data.source_ref,
            content=data.content,
            author=data.author,
            status="new",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        return self.create(feedback)


def make_feedback(
    *,
    status: str = "new",
    content: str = "大厅排队等待时间太长",
    author: str = "客户A",
    source: str = "hotline",
    created_at: datetime | None = None,
) -> Feedback:
    return Feedback(
        id=uuid.uuid4(),
        tenant_id="default",
        source=source,
        content=content,
        author=author,
        status=status,
        created_at=created_at or datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def repo() -> FakeFeedbackRepo:
    return FakeFeedbackRepo()


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


def make_service(session: FakeSession, repo: FakeFeedbackRepo) -> FeedbackService:
    return FeedbackService(session, repo=repo)


class TestCreate:
    def test_create_persists_and_commits(self, session: FakeSession, repo: FakeFeedbackRepo) -> None:
        service = make_service(session, repo)
        data = FeedbackCreate(source="app", content="APP 频繁闪退", author="客户B")

        feedback = service.create(data, tenant_id="tenant-1")

        assert feedback.status == "new"
        assert feedback.source == "app"
        assert feedback.content == "APP 频繁闪退"
        assert feedback.tenant_id == "tenant-1"
        assert len(repo.list_all()) == 1
        assert session.commits == 1

    def test_get_returns_none_when_missing(self, session: FakeSession, repo: FakeFeedbackRepo) -> None:
        service = make_service(session, repo)
        assert service.get(uuid.uuid4()) is None


class TestList:
    @pytest.fixture
    def seeded_repo(self) -> FakeFeedbackRepo:
        now = datetime.now(timezone.utc)
        return FakeFeedbackRepo(
            [
                make_feedback(status="new", source="hotline", content="排队太久", author="甲", created_at=now),
                make_feedback(status="analyzing", source="app", content="闪退问题", author="乙", created_at=now),
                make_feedback(status="resolved", source="hotline", content="材料复印很麻烦", author="甲", created_at=now),
                make_feedback(status="closed", source="website", content="预约爽约提醒", author="丙", created_at=now),
            ]
        )

    def test_list_all(self, session: FakeSession, seeded_repo: FakeFeedbackRepo) -> None:
        service = make_service(session, seeded_repo)
        result = service.list()
        assert result.total == 4
        assert len(result.items) == 4

    def test_list_filter_by_source(self, session: FakeSession, seeded_repo: FakeFeedbackRepo) -> None:
        service = make_service(session, seeded_repo)
        result = service.list(source="hotline")
        assert result.total == 2

    def test_list_filter_by_status(self, session: FakeSession, seeded_repo: FakeFeedbackRepo) -> None:
        service = make_service(session, seeded_repo)
        result = service.list(status="resolved")
        assert result.total == 1
        assert result.items[0].status == "resolved"

    def test_list_filter_by_keyword_in_content(self, session: FakeSession, seeded_repo: FakeFeedbackRepo) -> None:
        service = make_service(session, seeded_repo)
        result = service.list(keyword="排队")
        assert result.total == 1
        assert "排队" in result.items[0].content

    def test_list_pagination(self, session: FakeSession, seeded_repo: FakeFeedbackRepo) -> None:
        service = make_service(session, seeded_repo)
        result = service.list(params=PageParams(page=2, page_size=2))
        assert result.total == 4
        assert result.pages == 2
        assert len(result.items) == 2


class TestStatusFlow:
    def test_valid_transition(self, session: FakeSession, repo: FakeFeedbackRepo) -> None:
        service = make_service(session, repo)
        feedback = service.create(FeedbackCreate(content="测试"), tenant_id="default")
        result = service.change_status(feedback.id, "analyzing")
        assert result.status == "analyzing"
        assert session.commits == 2  # create 一次 + change_status 一次

    def test_invalid_transition_raises(self, session: FakeSession, repo: FakeFeedbackRepo) -> None:
        service = make_service(session, repo)
        feedback = service.create(FeedbackCreate(content="测试"), tenant_id="default")

        with pytest.raises(ValidationError) as exc_info:
            service.change_status(feedback.id, "replied")
        assert "非法状态流转" in exc_info.value.detail
        assert feedback.status == "new"

    def test_closed_is_terminal(self, session: FakeSession, repo: FakeFeedbackRepo) -> None:
        repo._items.append(make_feedback(status="closed"))
        service = make_service(session, repo)
        with pytest.raises(ValidationError):
            service.change_status(repo.list_all()[0].id, "new")

    def test_missing_feedback_raises_not_found(self, session: FakeSession, repo: FakeFeedbackRepo) -> None:
        service = make_service(session, repo)
        with pytest.raises(NotFoundError):
            service.change_status(uuid.uuid4(), "analyzing")


class TestBatchStatus:
    def test_batch_rolls_back_on_invalid(self, session: FakeSession, repo: FakeFeedbackRepo) -> None:
        repo._items.append(make_feedback(status="new"))
        repo._items.append(make_feedback(status="closed"))
        service = make_service(session, repo)
        ids = [item.id for item in repo.list_all()]

        with pytest.raises(ValidationError):
            service.batch_change_status(ids, "analyzing")

        assert session.rollbacks == 1
        # 第一个 feedback 的状态在内存对象上已被修改，但事务回滚后调用方应整体放弃；
        # 校验点：异常被抛出且未提交（commits 保持 0）。
        assert session.commits == 0

    def test_batch_all_valid_commits(self, session: FakeSession, repo: FakeFeedbackRepo) -> None:
        repo._items.append(make_feedback(status="new"))
        repo._items.append(make_feedback(status="analyzing"))
        service = make_service(session, repo)
        ids = [item.id for item in repo.list_all()]

        changed = service.batch_change_status(ids, "resolved")

        assert changed == 2
        assert session.commits == 1


class TestStats:
    def test_count_by_status(self, session: FakeSession, repo: FakeFeedbackRepo) -> None:
        repo._items += [
            make_feedback(status="new"),
            make_feedback(status="new"),
            make_feedback(status="resolved"),
        ]
        service = make_service(session, repo)
        counts = service.count_by_status()
        assert counts == {"new": 2, "resolved": 1}

    def test_pending_count(self, session: FakeSession, repo: FakeFeedbackRepo) -> None:
        repo._items += [
            make_feedback(status="new"),
            make_feedback(status="analyzing"),
            make_feedback(status="ai_reviewing"),
            make_feedback(status="closed"),
        ]
        service = make_service(session, repo)
        assert service.pending_count() == 3
        assert PENDING_STATUSES == {"new", "analyzing", "ai_reviewing"}