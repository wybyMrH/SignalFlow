"""SignalFlow 后端 - 业务服务层。

服务层编排领域逻辑与仓储访问，是 API 与 Workflow/LLM 之间的薄边界。
约定：Service 层不得直接 import langgraph / litellm，AI 调用统一通过
llm/gateway.py 抽象接口（或注入的网关协议）接入。
"""

from app.services.agents import AgentService
from app.services.automation import AutomationService
from app.services.base import ReplyGenerator, ServiceBase
from app.services.business import BusinessService
from app.services.dashboard import DashboardService
from app.services.feedback import FeedbackService
from app.services.gov import GovService
from app.services.insight import InsightService
from app.services.interview import InterviewService
from app.services.resources import ResourceService
from app.services.roadmap import RoadmapService
from app.services.settings import SettingsService
from app.services.workflows import WorkflowService

__all__ = [
    "ServiceBase",
    "ReplyGenerator",
    "FeedbackService",
    "InsightService",
    "DashboardService",
    "InterviewService",
    "BusinessService",
    "AutomationService",
    "AgentService",
    "WorkflowService",
    "ResourceService",
    "GovService",
    "RoadmapService",
    "SettingsService",
]