"""SignalFlow 后端 - 系统设置服务。

KV 配置读写（Setting）、渠道接入管理（ChannelConfig）与配置变更审计（AuditLog）。
配置表量级小，暂以内存查询；变更记录统一写入审计日志（同事务提交）。
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import NotFoundError, ValidationError
from app.models.audit import AuditLog
from app.models.setting import ChannelConfig, Setting
from app.repositories.setting import ChannelConfigRepository, SettingRepository
from app.services.base import ServiceBase
from sqlalchemy.orm import Session


class SettingsService(ServiceBase):
    """系统配置与渠道管理服务。"""

    def __init__(
        self,
        session: Session,
        *,
        setting_repo: SettingRepository | None = None,
        channel_repo: ChannelConfigRepository | None = None,
    ) -> None:
        super().__init__(session)
        self._setting_repo = setting_repo or SettingRepository(session)
        self._channel_repo = channel_repo or ChannelConfigRepository(session)

    # ──────────────────────────────────────────────
    # KV 配置
    # ──────────────────────────────────────────────

    def get_config(self, key: str) -> str | None:
        """按 key 读取配置值，不存在时返回 None。"""
        setting = self._find_by_key(key)
        return setting.value if setting is not None else None

    def get_config_or(self, key: str, default: str) -> str:
        """按 key 读取配置值，缺失时返回默认值。"""
        value = self.get_config(key)
        return value if value is not None else default

    def set_config(
        self,
        key: str,
        value: str,
        *,
        description: str | None = None,
        changed_by: str | None = None,
        ip_address: str | None = None,
    ) -> Setting:
        """写入/更新配置项并记录审计日志（CREATE 或 UPDATE）。

        value 允许空字符串，不允许 None（避免歧义）；key 不能为空。
        """
        if not key or not key.strip():
            raise ValidationError(detail="配置 key 不能为空")
        if value is None:  # type: ignore[redundant-expr]
            raise ValidationError(detail="配置 value 不能为 None")

        setting = self._find_by_key(key)
        old_value: str | None = None if setting is None else setting.value
        action = "CREATE" if setting is None else "UPDATE"
        if setting is None:
            setting = Setting(
                id=str(uuid.uuid4()),
                key=key,
                value=value,
                description=description,
                updated_at=datetime.now(timezone.utc),
            )
            self._setting_repo.create(setting)
        else:
            setting.value = value
            if description is not None:
                setting.description = description
            self._db.flush()

        self._write_audit(
            action=action,
            entity_type="Setting",
            entity_id=key,
            user_id=changed_by,
            details={"key": key, "old_value": old_value, "new_value": value},
            ip_address=ip_address,
        )
        self._commit()
        return setting

    def list_configs(self) -> list[Setting]:
        """返回全部配置项。"""
        return list(self._setting_repo.list_all())  # type: ignore[arg-type]

    def _find_by_key(self, key: str) -> Setting | None:
        """按 key 查找配置项（表量级小，内存线性查找）。"""
        for setting in self._setting_repo.list_all():  # type: ignore[arg-type]
            if setting.key == key:
                return setting
        return None

    # ──────────────────────────────────────────────
    # 渠道配置
    # ──────────────────────────────────────────────

    def list_channels(self) -> list[ChannelConfig]:
        """返回全部渠道配置。"""
        return list(self._channel_repo.list_all())  # type: ignore[arg-type]

    def toggle_channel(self, key: str) -> ChannelConfig:
        """切换渠道启用/停用状态。"""
        channel = self._find_channel(key)
        channel.enabled = not channel.enabled
        self._commit()
        return channel

    def mark_channel_sync(
        self,
        key: str,
        *,
        connected: bool | None = None,
        incoming_delta: int = 0,
    ) -> ChannelConfig:
        """记录渠道同步状态与增量（供渠道适配器回调）。"""
        channel = self._find_channel(key)
        if connected is not None:
            channel.connected = connected
        if incoming_delta:
            channel.incoming = (channel.incoming or 0) + incoming_delta
        channel.last_sync = datetime.now(timezone.utc)
        self._commit()
        return channel

    def _find_channel(self, key: str) -> ChannelConfig:
        """按 key 查找渠道配置，不存在时抛 NotFoundError。"""
        for channel in self._channel_repo.list_all():  # type: ignore[arg-type]
            if channel.key == key:
                return channel
        raise NotFoundError(resource="渠道配置")

    # ──────────────────────────────────────────────
    # 审计
    # ──────────────────────────────────────────────

    def _write_audit(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str,
        user_id: str | None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> None:
        """写入审计日志（随配置变更同事务提交）。"""
        log = AuditLog(
            id=str(uuid.uuid4()),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            details=json.dumps(details or {}, ensure_ascii=False),
            ip_address=ip_address,
        )
        self._db.add(log)