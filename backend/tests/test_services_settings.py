"""SignalFlow 后端 - SettingsService 单元测试。

覆盖 KV 配置读写与审计、渠道开关与同步、校验失败路径。
使用内存 mock，不依赖数据库。
"""

from __future__ import annotations

import json

import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.models.audit import AuditLog
from app.models.setting import ChannelConfig, Setting
from app.services.settings import SettingsService
from tests.mocks import FakeSession, MemoryRepo


USE_CREATE = object()


def make_setting(key: str, value: str) -> Setting:
    return Setting(id="s-1" if key == "s-1" else f"s-{key}", key=key, value=value, description=None)


def make_channel(key: str, *, enabled: bool = False, connected: bool = False) -> ChannelConfig:
    return ChannelConfig(
        id=f"c-{key}",
        key=key,
        label=key,
        enabled=enabled,
        connected=connected,
        incoming=0,
    )


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def setting_repo() -> MemoryRepo:
    return MemoryRepo([make_setting("existing_key", "old_value")])


@pytest.fixture
def channel_repo() -> MemoryRepo:
    return MemoryRepo([make_channel("hotline", enabled=True, connected=True)])


def make_service(
    session: FakeSession,
    setting_repo: MemoryRepo,
    channel_repo: MemoryRepo,
) -> SettingsService:
    return SettingsService(
        session,
        setting_repo=setting_repo,  # type: ignore[arg-type]
        channel_repo=channel_repo,  # type: ignore[arg-type]
    )


class TestConfig:
    def test_get_config(self, session: FakeSession, setting_repo: MemoryRepo, channel_repo: MemoryRepo) -> None:
        service = make_service(session, setting_repo, channel_repo)
        assert service.get_config("existing_key") == "old_value"
        assert service.get_config("missing_key") is None
        assert service.get_config_or("missing_key", "fallback") == "fallback"

    def test_set_config_creates_with_audit(
        self, session: FakeSession, setting_repo: MemoryRepo, channel_repo: MemoryRepo
    ) -> None:
        service = make_service(session, setting_repo, channel_repo)
        setting = service.set_config("new_key", "v1", description="说明", changed_by="user-1")

        assert setting.key == "new_key"
        assert setting.value == "v1"
        # 新配置已入 repo
        assert service.get_config("new_key") == "v1"
        # CREATE 审计日志写入（同事务）
        audits = [obj for obj in session.joined if isinstance(obj, AuditLog)]
        assert len(audits) == 1
        assert audits[0].action == "CREATE"
        assert audits[0].entity_type == "Setting"
        assert audits[0].entity_id == "new_key"
        assert json.loads(audits[0].details)["new_value"] == "v1"
        assert session.commits == 1

    def test_set_config_updates_existing_with_audit(
        self, session: FakeSession, setting_repo: MemoryRepo, channel_repo: MemoryRepo
    ) -> None:
        service = make_service(session, setting_repo, channel_repo)
        setting = service.set_config("existing_key", "new_value", changed_by="user-1")

        assert setting.value == "new_value"
        audits = [obj for obj in session.joined if isinstance(obj, AuditLog)]
        assert len(audits) == 1
        assert audits[0].action == "UPDATE"
        details = json.loads(audits[0].details)
        assert details["old_value"] == "old_value"
        assert details["new_value"] == "new_value"
        assert len(setting_repo.list_all()) == 1  # 不新增记录

    def test_set_config_invalid_key(self, session: FakeSession, setting_repo: MemoryRepo, channel_repo: MemoryRepo) -> None:
        service = make_service(session, setting_repo, channel_repo)
        with pytest.raises(ValidationError):
            service.set_config("", "v")

    def test_set_config_none_value(self, session: FakeSession, setting_repo: MemoryRepo, channel_repo: MemoryRepo) -> None:
        service = make_service(session, setting_repo, channel_repo)
        with pytest.raises(ValidationError):
            service.set_config("key", None)  # type: ignore[arg-type]

    def test_list_configs(self, session: FakeSession, setting_repo: MemoryRepo, channel_repo: MemoryRepo) -> None:
        service = make_service(session, setting_repo, channel_repo)
        assert len(service.list_configs()) == 1


class TestChannel:
    def test_toggle_channel(self, session: FakeSession, setting_repo: MemoryRepo, channel_repo: MemoryRepo) -> None:
        service = make_service(session, setting_repo, channel_repo)
        channel = service.toggle_channel("hotline")
        assert channel.enabled is False
        channel = service.toggle_channel("hotline")
        assert channel.enabled is True

    def test_toggle_missing_channel_raises(
        self, session: FakeSession, setting_repo: MemoryRepo, channel_repo: MemoryRepo
    ) -> None:
        service = make_service(session, setting_repo, channel_repo)
        with pytest.raises(NotFoundError):
            service.toggle_channel("missing-channel")

    def test_mark_channel_sync(self, session: FakeSession, setting_repo: MemoryRepo, channel_repo: MemoryRepo) -> None:
        service = make_service(session, setting_repo, channel_repo)
        channel = service.mark_channel_sync("hotline", connected=False, incoming_delta=5)
        assert channel.connected is False
        assert channel.incoming == 5
        assert channel.last_sync is not None

    def test_list_channels(self, session: FakeSession, setting_repo: MemoryRepo, channel_repo: MemoryRepo) -> None:
        service = make_service(session, setting_repo, channel_repo)
        assert [c.key for c in service.list_channels()] == ["hotline"]