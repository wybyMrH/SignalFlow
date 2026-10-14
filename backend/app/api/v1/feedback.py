"""SignalFlow 后端 - 反馈接口。

骨架阶段：提供创建反馈与读取反馈的最小 API 契约，
服务层落库后返回；AI 分析工作流在后续切片以异步方式接入。
"""

import uuid

from app.core.database import get_db
from app.schemas.feedback import FeedbackCreate, FeedbackRead
from app.services.feedback import FeedbackService
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter()


def _service(db: Session = Depends(get_db)) -> FeedbackService:
    return FeedbackService(db)


@router.post("", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
def create_feedback(payload: FeedbackCreate, service=Depends(_service)) -> FeedbackRead:
    """创建一条客户反馈并落库。"""
    created = service.create(payload)
    return FeedbackRead.model_validate(created)


@router.get("/{feedback_id}", response_model=FeedbackRead)
def get_feedback(feedback_id: uuid.UUID, service=Depends(_service)) -> FeedbackRead:
    """按 id 读取反馈。"""
    feedback = service.get(feedback_id)
    if feedback is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="feedback not found")
    return FeedbackRead.model_validate(feedback)