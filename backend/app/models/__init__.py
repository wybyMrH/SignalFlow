"""SignalFlow 后端 - 领域模型（SQLAlchemy ORM）。"""

from app.core.database import Base
from app.models.ai_ import AIChatMessage, AIWorkflowRun
from app.models.audit import AuditLog
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

__all__ = [
    "Base",
    "AIChatMessage",
    "AIWorkflowRun",
    "AuditLog",
    "AutomationRule",
    "ClassificationResult",
    "DedupGroup",
    "PriorityAdjustment",
    "PriorityRule",
    "BusinessLead",
    "CommonNeed",
    "MarketSignal",
    "Feedback",
    "GovAlertItem",
    "GovHotTopic",
    "GovPolicyNotice",
    "InsightTopic",
    "InterviewRecord",
    "ApiEndpointState",
    "DatabaseState",
    "ResourceAlert",
    "ServerState",
    "SystemLogEntry",
    "ReplyDraft",
    "RoadmapItem",
    "TaskItem",
    "ChannelConfig",
    "Setting",
    "User",
    "Workflow",
    "WorkflowRun",
]