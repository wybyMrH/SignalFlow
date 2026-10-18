"""SignalFlow 后端 - 反馈接口。

提供反馈列表（分页 + 筛选）、状态统计、创建、读取与状态流转 API，
对齐前端 FeedbackView / FeedbackStats 契约；AI 分析工作流在后续切片异步接入。
"""

import uuid

from app.core.database import get_db
from app.core.pagination import PageParams, PageResponse
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackRead,
    FeedbackStats,
    FeedbackStatusUpdate,
    FeedbackView,
)
from app.services.feedback import FeedbackService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

router = APIRouter()


def _service(db: Session = Depends(get_db)) -> FeedbackService:
    return FeedbackService(db)


def _to_view(feedback) -> FeedbackView:
    """ORM -> 前端 FeedbackView 契约（骨架扩展字段保持默认值）。"""
    return FeedbackView.model_validate(feedback)


@router.post("", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
def create_feedback(payload: FeedbackCreate, service=Depends(_service)) -> FeedbackRead:
    """创建一条客户反馈并落库。"""
    created = service.create(payload)
    return FeedbackRead.model_validate(created)


@router.get("", response_model=PageResponse[FeedbackView])
def list_feedbacks(
    source: str | None = Query(default=None, description="来源渠道过滤"),
    feedback_status: str | None = Query(default=None, alias="status", description="状态过滤"),
    keyword: str | None = Query(default=None, description="内容/作者关键词"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    service=Depends(_service),
) -> PageResponse[FeedbackView]:
    """反馈列表（分页 + 来源/状态/关键词筛选）。"""
    params = PageParams(page=page, page_size=page_size)
    result = service.list(
        source=source,
        status=feedback_status,
        keyword=keyword,
        params=params,
    )
    return PageResponse(
        items=[_to_view(item) for item in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        pages=result.pages,
    )


@router.get("/stats", response_model=FeedbackStats)
def get_feedback_stats(service=Depends(_service)) -> FeedbackStats:
    """反馈状态统计（各生命周期状态数量）。"""
    counts = service.count_by_status()
    return FeedbackStats(
        total=sum(counts.values()),
        new=counts.get("new", 0),
        analyzing=counts.get("analyzing", 0),
        ai_reviewing=counts.get("ai_reviewing", 0),
        ai_replied=counts.get("ai_replied", 0),
        resolved=counts.get("resolved", 0),
        replied=counts.get("replied", 0),
        closed=counts.get("closed", 0),
        # 高优先级信号：priority >= 4 的反馈数（与前端 mock 统计口径一致）
        high_priority=service.high_priority_count(),
    )


@router.get("/{feedback_id}", response_model=FeedbackRead)
def get_feedback(feedback_id: uuid.UUID, service=Depends(_service)) -> FeedbackRead:
    """按 id 读取反馈。"""
    feedback = service.get(feedback_id)
    if feedback is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="feedback not found")
    return FeedbackRead.model_validate(feedback)


@router.patch("/{feedback_id}/status", response_model=FeedbackView)
def update_feedback_status(
    feedback_id: uuid.UUID,
    payload: FeedbackStatusUpdate,
    service=Depends(_service),
) -> FeedbackView:
    """反馈状态流转（按状态机校验；reviewer/reply_content 留待分析切片回填）。"""
    feedback = service.change_status(feedback_id, payload.status)
    return _to_view(feedback)