"""SignalFlow 后端 - 数据访问层（Repository）。

Repository 负责将 ORM 操作封装为可测试、可替换的仓储接口；
服务层只依赖 Repository，不直接操作 Session。
"""

from app.repositories.ai_ import AIChatMessageRepository, AIWorkflowRunRepository
from app.repositories.agent import AgentRepository, AgentToolRepository, SkillRepository
from app.repositories.automation import (
    AutomationRuleRepository,
    ClassificationResultRepository,
    DedupGroupRepository,
    PriorityAdjustmentRepository,
    PriorityRuleRepository,
)
from app.repositories.base import BaseRepository
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
from app.repositories.roadmap import ReplyDraftRepository, RoadmapItemRepository, TaskItemRepository
from app.repositories.setting import ChannelConfigRepository, SettingRepository
from app.repositories.user import UserRepository
from app.repositories.workflow import WorkflowRepository, WorkflowRunRepository

__all__ = [
    "BaseRepository",
    "AIChatMessageRepository",
    "AIWorkflowRunRepository",
    "AgentRepository",
    "AgentToolRepository",
    "SkillRepository",
    "AutomationRuleRepository",
    "ClassificationResultRepository",
    "DedupGroupRepository",
    "PriorityAdjustmentRepository",
    "PriorityRuleRepository",
    "BusinessLeadRepository",
    "CommonNeedRepository",
    "MarketSignalRepository",
    "FeedbackRepository",
    "GovAlertItemRepository",
    "GovHotTopicRepository",
    "GovPolicyNoticeRepository",
    "InsightTopicRepository",
    "InterviewRecordRepository",
    "ApiEndpointStateRepository",
    "DatabaseStateRepository",
    "ResourceAlertRepository",
    "ServerStateRepository",
    "SystemLogEntryRepository",
    "ReplyDraftRepository",
    "RoadmapItemRepository",
    "TaskItemRepository",
    "ChannelConfigRepository",
    "SettingRepository",
    "UserRepository",
    "WorkflowRepository",
    "WorkflowRunRepository",
]