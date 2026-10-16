"""SignalFlow 后端 - 客户访谈接口。

列表 / 统计 / AI 提炼三个端点，对齐前端 InterviewRecord 契约：
ORM 的 datetime 字段需转 ISO 字符串，extraction 为 JSON dict 直接透传。
"""

from typing import Any

from app.core.database import get_db
from app.services.interview import InterviewService
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()


class _ExtractionBody(BaseModel):
    """AI 提炼请求体。

    前端以无 body POST 调用，骨架阶段全部字段可选；
    无 body 时保存空提炼并触发状态流转（recorded -> extracted）。
    """

    pain_points: list[str] | None = None
    needs: list[str] | None = None
    cooperation_intent: str | None = None
    matched_needs: list[str] | None = None
    lead_candidate: bool | None = None
    lead_reason: str | None = None


def _service(db: Session = Depends(get_db)) -> InterviewService:
    return InterviewService(db)


def _interview_to_dict(record: Any) -> dict[str, Any]:
    """ORM -> 前端契约字典。"""
    return {
        "id": record.id,
        "company_name": record.company_name,
        "company_type": record.company_type,
        "industry": record.industry,
        "contact_name": record.contact_name,
        "contact_role": record.contact_role,
        "interview_date": record.interview_date.isoformat() if record.interview_date else None,
        "duration_min": record.duration_min,
        "source": record.source,
        "status": record.status,
        "summary": record.summary,
        "key_points": record.key_points or [],
        "extraction": record.extraction,
        "linked_feedback_ids": record.linked_feedback_ids or [],
        "linked_lead_id": record.linked_lead_id,
        "recorder": record.recorder,
    }


@router.get("")
def list_interviews(service=Depends(_service)) -> list[dict]:
    """访谈记录列表（按访谈日期倒序）。"""
    return [_interview_to_dict(record) for record in service.list()]


@router.get("/summary")
def get_interview_summary(service=Depends(_service)) -> dict:
    """访谈统计总览。"""
    return service.summary()


@router.post("/{interview_id}/extract")
def run_interview_extraction(
    interview_id: str,
    payload: _ExtractionBody | None = None,
    service=Depends(_service),
) -> dict:
    """对访谈执行 AI 提炼（骨架：保存提炼并流转状态，可能联动生成线索）。"""
    body = payload or _ExtractionBody()
    extraction = body.model_dump(exclude_none=True)
    record = service.run_extraction(interview_id, extraction)
    return _interview_to_dict(record)