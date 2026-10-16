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


# ───── 自动化中心 ─────

@router.get("/automation/classification")
def get_auto_classification() -> list[dict]:
    """自动分类结果列表。"""
    return _ai_service.get_auto_classification()


@router.get("/automation/dedup")
def get_dedup_groups() -> list[dict]:
    """去重合并组列表。"""
    return _ai_service.get_dedup_groups()


@router.get("/automation/priority-rules")
def get_priority_rules() -> list[dict]:
    """优先级评分规则列表（RICE 模型）。"""
    return _ai_service.get_priority_rules()


@router.get("/automation/priority-adjustments")
def get_priority_adjustments() -> list[dict]:
    """优先级调整记录。"""
    return _ai_service.get_priority_adjustments()


@router.get("/automation/summary")
def get_automation_summary() -> dict:
    """自动化执行概览（日维度）。"""
    return _ai_service.get_automation_summary()


# ───── 商务洞察 ─────

@router.get("/business/leads")
def get_business_leads() -> list[dict]:
    """企业合作线索列表。"""
    return _ai_service.get_business_leads()


@router.get("/business/industries")
def get_industry_shares() -> list[dict]:
    """行业分布。"""
    return _ai_service.get_industry_shares()


@router.get("/business/signals")
def get_market_signals() -> list[dict]:
    """市场动向信号。"""
    return _ai_service.get_market_signals()


@router.get("/business/common-needs")
def get_common_needs() -> list[dict]:
    """共性需求归纳。"""
    return _ai_service.get_common_needs()


@router.get("/business/summary")
def get_business_summary() -> dict:
    """商务洞察总览。"""
    return _ai_service.get_business_summary()
