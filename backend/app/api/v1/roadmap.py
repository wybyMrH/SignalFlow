"""SignalFlow 后端 - 产品路线图接口。

提供路线图看板、任务管理与回复草稿状态流转，对齐前端 RoadmapBoard / TaskItem / ReplyDraft 契约。
"""

from typing import Any

from app.core.database import get_db
from app.services.roadmap import RoadmapService
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()


class _CreateTaskBody(BaseModel):
    """创建任务请求体。"""

    roadmap_id: str
    title: str
    owner: str
    priority: int = 0


class _StatusBody(BaseModel):
    """状态流转请求体。"""

    status: str


def _service(db: Session = Depends(get_db)) -> RoadmapService:
    return RoadmapService(db)


def _item_to_dict(item: Any) -> dict[str, Any]:
    """ORM -> 前端 RoadmapItem 契约。"""
    return {
        "id": item.id,
        "title": item.title,
        "topic_id": item.topic_id,
        "status": item.status,
        "version": item.version,
        "owner": item.owner,
        "due_date": item.due_date.isoformat() if item.due_date else None,
        "progress": item.progress or 0,
        "task_count": item.task_count or 0,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def _task_to_dict(task: Any) -> dict[str, Any]:
    """ORM -> 前端 TaskItem 契约。"""
    return {
        "id": task.id,
        "roadmap_id": task.roadmap_id,
        "title": task.title,
        "status": task.status,
        "owner": task.owner,
        "priority": task.priority or 0,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }


def _draft_to_dict(draft: Any) -> dict[str, Any]:
    """ORM -> 前端 ReplyDraft 契约。"""
    return {
        "id": draft.id,
        "feedback_id": draft.feedback_id,
        "excerpt": draft.excerpt,
        "draft": draft.draft,
        "tone": draft.tone,
        "status": draft.status,
        "updated_at": draft.updated_at.isoformat() if draft.updated_at else None,
    }


@router.get("/board")
def get_roadmap_board(service=Depends(_service)) -> dict:
    """路线图看板数据。"""
    items = service.list_items()
    tasks = list(service._tasks.list_all())  # type: ignore[arg-type]
    drafts = list(service._drafts.list_all())  # type: ignore[arg-type]
    return {
        "items": [_item_to_dict(i) for i in items],
        "tasks": [_task_to_dict(t) for t in tasks],
        "drafts": [_draft_to_dict(d) for d in drafts],
        "summary": service.summary(),
    }


@router.post("/tasks")
def create_task(payload: _CreateTaskBody, service=Depends(_service)) -> dict:
    """新建路线图任务。"""
    task = service.add_task(
        payload.roadmap_id,
        payload.title,
        owner=payload.owner,
        priority=payload.priority,
    )
    return _task_to_dict(task)


@router.patch("/tasks/{task_id}/status")
def update_task_status(task_id: str, payload: _StatusBody, service=Depends(_service)) -> dict:
    """任务状态流转。"""
    task = service.update_task_status(task_id, payload.status)
    return _task_to_dict(task)


@router.patch("/drafts/{draft_id}/status")
def update_draft_status(draft_id: str, payload: _StatusBody, service=Depends(_service)) -> dict:
    """草稿状态流转（draft → approved → sent）。"""
    draft = service._drafts.get_by_id(draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="草稿不存在")
    draft.status = payload.status
    service._commit()
    return _draft_to_dict(draft)
