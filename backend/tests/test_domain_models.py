"""SignalFlow 后端 - 阶段 1：所有 Domain 的 CRUD 基架验证。

使用嵌套事务（SAVEPOINT）保证测试隔离，测试结束后自动回滚清除数据。
验证目标：每个 Domain 的 Repository 可独立完成 create / get_by_id / count / delete。
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.ai_ import AIChatMessage, AIWorkflowRun
from app.models.automation import (
    AutomationRule,
    ClassificationResult,
    DedupGroup,
    PriorityAdjustment,
    PriorityRule,
)
from app.models.business import BusinessLead, CommonNeed, MarketSignal
from app.models.feedback import Feedback
from app.models.gov import GovAlertItem, GovHotTopic, GovPolicyNotice
from app.models.insight import InsightTopic
from app.models.interview import InterviewRecord
from app.models.resource import (
    ApiEndpointState,
    DatabaseState,
    ResourceAlert,
    ServerState,
    SystemLogEntry,
)
from app.models.roadmap import ReplyDraft, RoadmapItem, TaskItem
from app.models.setting import ChannelConfig, Setting
from app.models.user import User
from app.models.workflow import Workflow, WorkflowRun
from app.repositories.ai_ import AIChatMessageRepository, AIWorkflowRunRepository
from app.repositories.automation import (
    AutomationRuleRepository,
    ClassificationResultRepository,
    DedupGroupRepository,
    PriorityAdjustmentRepository,
    PriorityRuleRepository,
)
from app.repositories.business import (
    BusinessLeadRepository,
    CommonNeedRepository,
    MarketSignalRepository,
)
from app.repositories.feedback import FeedbackRepository
from app.repositories.gov import (
    GovAlertItemRepository,
    GovHotTopicRepository,
    GovPolicyNoticeRepository,
)
from app.repositories.insight import InsightTopicRepository
from app.repositories.interview import InterviewRecordRepository
from app.repositories.resource import (
    ApiEndpointStateRepository,
    DatabaseStateRepository,
    ResourceAlertRepository,
    ServerStateRepository,
    SystemLogEntryRepository,
)
from app.repositories.roadmap import (
    ReplyDraftRepository,
    RoadmapItemRepository,
    TaskItemRepository,
)
from app.repositories.setting import ChannelConfigRepository, SettingRepository
from app.repositories.user import UserRepository
from app.repositories.workflow import WorkflowRepository, WorkflowRunRepository

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    """提供嵌套事务隔离的数据库会话。"""
    session: Session = SessionLocal()
    session.begin_nested()  # SAVEPOINT
    try:
        yield session
    finally:
        session.rollback()  # 回滚到 SAVEPOINT，清除测试数据
        session.close()


# ---------------------------------------------------------------------------
# 辅助函数：通用 CRUD 验证
# ---------------------------------------------------------------------------

def _assert_crud(repo, model_cls, **kwargs):
    """对任意 Repository 执行 create → get_by_id → count → delete 验证。

    Args:
        repo: 已实例化的 Repository（继承 BaseRepository）。
        model_cls: 对应的 ORM 模型类，用于构造实例。
        **kwargs: 构造模型实例所需的最小必填字段。
    """
    # create
    obj = model_cls(**kwargs)
    created = repo.create(obj)
    repo._db.flush()
    assert created.id is not None

    # read
    fetched = repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id

    # count 至少为 1
    assert repo.count() >= 1

    # delete
    repo.delete(fetched)
    repo._db.flush()
    assert repo.get_by_id(created.id) is None


# ---------------------------------------------------------------------------
# 逐个 Domain 测试
# ---------------------------------------------------------------------------

def test_user_crud(db: Session):
    _assert_crud(
        UserRepository(db),
        User,
        username='testuser',
    )


def test_feedback_crud(db: Session):
    _assert_crud(
        FeedbackRepository(db),
        Feedback,
        content='test feedback',
        source='manual',
        tenant_id='default',
    )


def test_insight_topic_crud(db: Session):
    _assert_crud(
        InsightTopicRepository(db),
        InsightTopic,
        title='test topic',
    )


def test_roadmap_item_crud(db: Session):
    _assert_crud(
        RoadmapItemRepository(db),
        RoadmapItem,
        title='test roadmap',
    )


def test_task_item_crud(db: Session):
    _assert_crud(
        TaskItemRepository(db),
        TaskItem,
        title='test task',
        roadmap_id='r-001',
    )


def test_reply_draft_crud(db: Session):
    _assert_crud(
        ReplyDraftRepository(db),
        ReplyDraft,
        feedback_id='f-001',
        draft='draft content',
    )


def test_automation_rule_crud(db: Session):
    _assert_crud(
        AutomationRuleRepository(db),
        AutomationRule,
        name='test rule',
    )


def test_classification_result_crud(db: Session):
    _assert_crud(
        ClassificationResultRepository(db),
        ClassificationResult,
        feedback_id='f-001',
        suggested_topic='topic A',
    )


def test_dedup_group_crud(db: Session):
    _assert_crud(
        DedupGroupRepository(db),
        DedupGroup,
        representative_id='f-001',
    )


def test_priority_rule_crud(db: Session):
    _assert_crud(
        PriorityRuleRepository(db),
        PriorityRule,
        name='test priority',
    )


def test_priority_adjustment_crud(db: Session):
    _assert_crud(
        PriorityAdjustmentRepository(db),
        PriorityAdjustment,
        feedback_id='f-001',
        old_priority=1,
        new_priority=3,
    )


def test_workflow_crud(db: Session):
    _assert_crud(
        WorkflowRepository(db),
        Workflow,
        name='test workflow',
    )


def test_workflow_run_crud(db: Session):
    _assert_crud(
        WorkflowRunRepository(db),
        WorkflowRun,
        workflow_id='w-001',
    )


def test_business_lead_crud(db: Session):
    _assert_crud(
        BusinessLeadRepository(db),
        BusinessLead,
        feedback_id='f-001',
        content='need',
        company_name='Acme',
    )


def test_market_signal_crud(db: Session):
    _assert_crud(
        MarketSignalRepository(db),
        MarketSignal,
        title='signal',
    )


def test_common_need_crud(db: Session):
    _assert_crud(
        CommonNeedRepository(db),
        CommonNeed,
        title='common need',
    )


def test_interview_record_crud(db: Session):
    _assert_crud(
        InterviewRecordRepository(db),
        InterviewRecord,
        company_name='Acme',
    )


def test_gov_hot_topic_crud(db: Session):
    _assert_crud(
        GovHotTopicRepository(db),
        GovHotTopic,
        title='hot topic',
    )


def test_gov_alert_item_crud(db: Session):
    _assert_crud(
        GovAlertItemRepository(db),
        GovAlertItem,
        title='alert',
    )


def test_gov_policy_notice_crud(db: Session):
    _assert_crud(
        GovPolicyNoticeRepository(db),
        GovPolicyNotice,
        title='notice',
        content='content',
    )


def test_server_state_crud(db: Session):
    _assert_crud(
        ServerStateRepository(db),
        ServerState,
        name='srv-01',
    )


def test_database_state_crud(db: Session):
    _assert_crud(
        DatabaseStateRepository(db),
        DatabaseState,
        name='postgres',
    )


def test_api_endpoint_state_crud(db: Session):
    _assert_crud(
        ApiEndpointStateRepository(db),
        ApiEndpointState,
        method='GET',
        path='/test',
    )


def test_system_log_entry_crud(db: Session):
    _assert_crud(
        SystemLogEntryRepository(db),
        SystemLogEntry,
        message='log msg',
    )


def test_resource_alert_crud(db: Session):
    _assert_crud(
        ResourceAlertRepository(db),
        ResourceAlert,
        title='alert',
    )


def test_setting_crud(db: Session):
    _assert_crud(
        SettingRepository(db),
        Setting,
        key='mock_mode',
    )


def test_channel_config_crud(db: Session):
    _assert_crud(
        ChannelConfigRepository(db),
        ChannelConfig,
        key=f'channel-test-{uuid.uuid4().hex[:8]}',
        label='测试渠道',
    )


def test_ai_chat_message_crud(db: Session):
    _assert_crud(
        AIChatMessageRepository(db),
        AIChatMessage,
        session_id='s-001',
        content='hello',
    )


def test_ai_workflow_run_crud(db: Session):
    _assert_crud(
        AIWorkflowRunRepository(db),
        AIWorkflowRun,
        workflow_id='w-001',
    )
