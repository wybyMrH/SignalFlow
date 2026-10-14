"""SignalFlow 后端 - AI 工作流相关的 Pydantic Schema。

AI 对话、工作流状态、自动化规则、回复生成等对外契约。
字段变化需同步更新前端 types 与 API 文档。
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ────────── AI 工作流状态 ──────────

class AIWorkflowStatus(BaseModel):
    """AI 工作流运行状态。"""

    id: str
    name: str
    status: Literal["running", "completed", "failed", "queued"]
    progress: int = Field(ge=0, le=100)
    started_at: datetime
    eta: str | None = None
    detail: str | None = None


# ────────── AI 自动化规则 ──────────

class AIAutomationRule(BaseModel):
    """AI 自动化规则配置。"""

    id: str
    name: str
    description: str
    enabled: bool
    scenario: str
    icon: str
    tone: Literal["primary", "success", "warning", "info", "danger"]
    stats: str | None = None


# ────────── AI 对话 ──────────

class AIChatMessage(BaseModel):
    """AI 对话消息。"""

    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    workflow_refs: list[str] | None = None
    sources: list[str] | None = None


class AIChatRequest(BaseModel):
    """AI 对话请求体。"""

    query: str
    history: list[AIChatMessage] = Field(default_factory=list)


# ────────── 回复生成 ──────────

class ReplyDraftRequest(BaseModel):
    """AI 生成回复草稿请求。"""

    content: str


class ReplySuggestionRequest(BaseModel):
    """AI 回复建议请求。"""

    content: str


class AutoApproveResponse(BaseModel):
    """AI 自动审批响应。"""

    reply: str
    status: str
