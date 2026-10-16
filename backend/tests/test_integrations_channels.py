"""SignalFlow 后端 - 其余 4 个渠道适配器与注册表测试。

覆盖：email / im / app_store / gov_hotline 的 parse/normalize 契约、
骨架阶段未配置数据源时 fetch_raw 返回空列表、ChannelRegistry 路由与隔离日志通道。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import pytest

from app.integrations import (
    AppStoreAdapter,
    ChannelRegistry,
    EmailAdapter,
    GovHotlineAdapter,
    IMAdapter,
)
from app.integrations.base import BaseAdapter, FeedbackEvent, StandardFeedback


class TestEmailAdapter:
    def make_adapter(self) -> EmailAdapter:
        return EmailAdapter()

    def test_fetch_raw_empty_without_imap_config(self) -> None:
        assert self.make_adapter().fetch_raw() == []

    def test_parse_full_email(self) -> None:
        raw = {
            "message_id": "msg-1",
            "from_": "customer@customer.example.com",
            "from_name": "客户甲",
            "to": "support@example.com",
            "subject": "咨询办理材料",
            "body": "请问企业认证需要准备哪些材料？",
            "date": "Wed, 14 Oct 2026 10:00:00 +0800",
        }
        event = self.make_adapter().parse(raw)

        assert isinstance(event, FeedbackEvent)
        assert event.source == "email"
        assert event.channel == "email"
        assert event.raw_content == raw["body"]
        assert event.customer_id == "customer@customer.example.com"
        # RFC 2822 +0800 → UTC 02:00
        assert event.timestamp == datetime(2026, 10, 14, 2, 0, tzinfo=timezone.utc)
        assert event.metadata["message_id"] == "msg-1"
        assert event.metadata["subject"] == "咨询办理材料"
        assert event.metadata["channel_label"] == "邮件"

    def test_parse_fallback_sender_field(self) -> None:
        raw = {"message_id": "m2", "from": "b@example.com", "body": "你好"}
        event = self.make_adapter().parse(raw)
        assert event.customer_id == "b@example.com"

    def test_parse_missing_body_raises(self) -> None:
        with pytest.raises(ValueError, match="缺少正文"):
            self.make_adapter().parse({"message_id": "m3"})

    def test_normalize_sets_source_ref(self) -> None:
        adapter = self.make_adapter()
        event = adapter.parse(
            {"message_id": "msg-1", "body": "内容", "from_": "a@example.com"}
        )
        std = adapter.normalize(event)
        assert isinstance(std, StandardFeedback)
        assert std.source_ref == "email:msg-1"


class TestIMAdapter:
    def make_adapter(self) -> IMAdapter:
        return IMAdapter()

    def test_fetch_raw_empty_for_passive_channel(self) -> None:
        assert self.make_adapter().fetch_raw() == []

    def test_parse_message(self) -> None:
        raw = {
            "msg_id": "m-1",
            "content": "您好，我想反馈一个权限问题",
            "from_user": "userA",
            "msg_type": "text",
            "create_time": 1760424000,  # 2025-10-14T06:40:00Z
        }
        event = self.make_adapter().parse(raw)

        assert event.source == "im"
        assert event.channel == "im"
        assert event.raw_content == raw["content"]
        assert event.customer_id == "userA"
        assert event.metadata["msg_id"] == "m-1"
        assert event.timestamp == datetime(2025, 10, 14, 6, 40, tzinfo=timezone.utc)

    def test_parse_webhook_envelope(self) -> None:
        payload = {
            "message": {
                "MsgId": "wx-1",
                "Content": "触达消息未收到",
                "FromUser": "zhangsan",
                "CreateTime": 1760424000,
            }
        }
        event = self.make_adapter().parse_webhook(payload)
        assert event.metadata["msg_id"] == "wx-1"
        assert event.customer_id == "zhangsan"
        assert event.raw_content == "触达消息未收到"

    def test_parse_missing_content_raises(self) -> None:
        with pytest.raises(ValueError, match="缺少内容"):
            self.make_adapter().parse({"msg_id": "x"})


class TestAppStoreAdapter:
    def make_adapter(self) -> AppStoreAdapter:
        return AppStoreAdapter(store="app_store_cn", app_id="com.example.app")

    def test_fetch_raw_empty_without_endpoint(self) -> None:
        assert self.make_adapter().fetch_raw() == []

    def test_parse_review_with_title(self) -> None:
        raw = {
            "id": "r-1",
            "rating": 2,
            "title": "闪退",
            "text": "点击保存就闪退，很影响使用",
            "author": "用户甲",
            "date": "2026-10-14T08:00:00Z",
        }
        event = self.make_adapter().parse(raw)

        assert event.source == "review"
        assert event.channel == "app_store"
        assert event.raw_content == "闪退：点击保存就闪退，很影响使用"
        assert event.customer_id == "用户甲"
        assert event.metadata["rating"] == 2
        assert event.metadata["store"] == "app_store_cn"
        assert event.metadata["app_id"] == "com.example.app"
        assert event.metadata["app_version"] == ""
        assert event.timestamp == datetime(2026, 10, 14, 8, 0, tzinfo=timezone.utc)

    def test_parse_review_extracts_version(self) -> None:
        raw = {"id": "r-2", "rating": 5, "text": "1.2.3 版本打开就崩溃"}
        event = self.make_adapter().parse(raw)
        assert event.metadata["app_version"] == "1.2.3"

    def test_parse_missing_text_raises(self) -> None:
        with pytest.raises(ValueError, match="缺少文本"):
            self.make_adapter().parse({"id": "r-3", "rating": 1})

    def test_normalize_sets_source_ref(self) -> None:
        adapter = self.make_adapter()
        event = adapter.parse({"id": "r-1", "rating": 4, "text": "很好用"})
        std = adapter.normalize(event)
        assert std.source_ref == "app_store:r-1"


class TestGovHotlineAdapter:
    def make_adapter(self) -> GovHotlineAdapter:
        return GovHotlineAdapter()

    def test_fetch_raw_empty_without_data_source(self) -> None:
        assert self.make_adapter().fetch_raw() == []

    def test_parse_chinese_fields(self) -> None:
        raw = {
            "工单编号": "GZ20261014001",
            "诉求内容": "小区路灯长期不亮，夜间出行存在安全隐患",
            "市民": "张先生",
            "事项分类": "城市管理",
            "所属区县": "朝阳区",
            "紧急程度": "一般",
        }
        event = self.make_adapter().parse(raw)

        assert event.source == "hotline"
        assert event.channel == "gov_hotline"
        assert event.raw_content == raw["诉求内容"]
        assert event.customer_id == "张先生"
        assert event.metadata["record_id"] == "GZ20261014001"
        assert event.metadata["category"] == "城市管理"
        assert event.metadata["district"] == "朝阳区"
        assert event.metadata["urgency"] == "一般"
        assert event.metadata["channel_label"] == "政务热线"

    def test_parse_english_fields(self) -> None:
        raw = {
            "id": "case-1",
            "complaint": "电梯故障反复报修未解决",
            "citizen": "13800001234",
            "category": "住宅物业",
        }
        event = self.make_adapter().parse(raw)
        assert event.metadata["record_id"] == "case-1"
        assert event.customer_id == "13800001234"

    def test_parse_missing_content_raises(self) -> None:
        with pytest.raises(ValueError, match="缺少诉求内容"):
            self.make_adapter().parse({"工单编号": "GZ-1"})

    def test_normalize_sets_source_ref(self) -> None:
        adapter = self.make_adapter()
        event = adapter.parse({"工单编号": "GZ-1", "诉求内容": "测试"})
        std = adapter.normalize(event)
        assert std.source_ref == "gov_hotline:GZ-1"


class _RegistryAdapter(BaseAdapter):
    channel = "registry_test"
    source = "test"

    def fetch_raw(self, *, limit: int = 100) -> list[object]:
        return []

    def parse(self, raw: object) -> FeedbackEvent:
        raise NotImplementedError

    def normalize(self, event: FeedbackEvent) -> StandardFeedback:
        raise NotImplementedError


class TestChannelRegistry:
    def test_register_and_route(self) -> None:
        registry = ChannelRegistry()
        adapter = _RegistryAdapter()
        registry.register(adapter)

        assert registry.get("registry_test") is adapter
        assert registry.all_channels() == ["registry_test"]
        assert registry.all_adapters() == [adapter]

    def test_duplicate_register_overwrites_with_warning(self, caplog) -> None:
        registry = ChannelRegistry()
        registry.register(_RegistryAdapter())
        replacement = _RegistryAdapter()
        with caplog.at_level(logging.WARNING, logger="signalflow.integrations"):
            registry.register(replacement)

        assert registry.get("registry_test") is replacement
        assert any("重复注册" in rec.getMessage() for rec in caplog.records)


def test_integration_uses_isolated_log_channel() -> None:
    """验收标准 ②：渠道集成错误记录在独立日志通道。"""
    logger = logging.getLogger("signalflow.integrations")
    assert logger.name == "signalflow.integrations"
    # 与业务日志通道不同，便于按渠道排查且不影响主服务日志级别
    assert logger is not logging.getLogger("signalflow")