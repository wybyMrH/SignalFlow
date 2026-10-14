"""SignalFlow 后端 - AI 工作流接口。

提供 AI 对话、工作流状态查询、自动化规则管理、回复生成等 API。
骨架阶段使用 mock 服务实现；真实 LLM 接入时替换 service 内部逻辑即可。
"""

from app.schemas.ai import (
    AIAutomationRule,
    AIChatMessage,
    AIChatRequest,
    AIWorkflowStatus,
    AutoApproveResponse,
    ReplyDraftRequest,
    ReplySuggestionRequest,
)
from app.services.ai import AIService
from fastapi import APIRouter

router = APIRouter()

# 单例服务（mock 阶段无状态，可复用）
_ai_service = AIService()


@router.get("/workflows", response_model=list[AIWorkflowStatus])
def get_ai_workflows() -> list[AIWorkflowStatus]:
    """获取当前 AI 工作流运行状态列表。"""
    return _ai_service.get_workflows()


@router.get("/automation-rules", response_model=list[AIAutomationRule])
def get_ai_automation_rules() -> list[AIAutomationRule]:
    """获取 AI 自动化规则配置列表。"""
    return _ai_service.get_automation_rules()


@router.post("/chat", response_model=AIChatMessage)
def chat_with_ai(payload: AIChatRequest) -> AIChatMessage:
    """AI 对话：接收用户查询，返回助手回复。"""
    return _ai_service.chat(payload.query, payload.history)


@router.get("/chat/welcome", response_model=AIChatMessage)
def get_ai_welcome() -> AIChatMessage:
    """获取 AI 欢迎语。"""
    return _ai_service.welcome()


@router.post("/reply-draft")
def generate_reply_draft(payload: ReplyDraftRequest) -> str:
    """基于反馈内容生成 AI 回复草稿。"""
    return _ai_service.generate_reply(payload.content)


@router.post("/reply-suggestion")
def get_reply_suggestion(payload: ReplySuggestionRequest) -> str:
    """AI 气泡助手：获取简短回复建议。"""
    return _ai_service.get_reply_suggestion(payload.content)


@router.post("/auto-approve/{feedback_id}", response_model=AutoApproveResponse)
def auto_approve_feedback(feedback_id: str, payload: ReplyDraftRequest) -> AutoApproveResponse:
    """AI 自动审批：生成统一话术回复并标记状态。"""
    result = _ai_service.auto_approve(feedback_id, payload.content)
    return AutoApproveResponse(reply=result["reply"], status=result["status"])
