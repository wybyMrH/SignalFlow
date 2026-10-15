"""SignalFlow 后端 - 产品路线图服务。

产品里程碑（RoadmapItem）与子任务管理、任务优先级重算、回复草稿管理。
依赖洞察主题（insights_repo）将高分主题转成路线图项目并推导优先级。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import NotFoundError, ValidationError
from app.models.insight import InsightTopic
from app.models.roadmap import ReplyDraft, RoadmapItem, TaskItem
from app.repositories.insight import InsightTopicRepository
from app.repositories.roadmap import ReplyDraftRepository, RoadmapItemRepository, TaskItemRepository
from app.services.base import ServiceBase
from sqlalchemy.orm import Session

# 路线图状态机（planning → active → done / cancelled）
ROADMAP_STATUS_FLOW: dict[str, set[str]] = {
    "planning": {"active", "done", "cancelled"},
    "active": {"done", "cancelled"},
    "done": set(),
    "cancelled": set(),
}

# 任务状态机（todo → doing → done）
TASK_STATUS_FLOW: dict[str, set[str]] = {
    "todo": {"doing", "done"},
    "doing": {"done"},
    "done": set(),
}


class RoadmapService(ServiceBase):
    """产品路线图、任务与回复草稿服务。"""

    def __init__(
        self,
        session: Session,
        *,
        repo: RoadmapItemRepository | None = None,
        task_repo: TaskItemRepository | None = None,
        draft_repo: ReplyDraftRepository | None = None,
        insight_repo: InsightTopicRepository | None = None,
    ) -> None:
        super().__init__(session)
        self._repo = repo or RoadmapItemRepository(session)
        self._tasks = task_repo or TaskItemRepository(session)
        self._drafts = draft_repo or ReplyDraftRepository(session)
        self._insights = insight_repo or InsightTopicRepository(session)

    # ──────────────────────────────────────────────
    # 优先级推导（纯函数）
    # ──────────────────────────────────────────────

    @staticmethod
    def compute_recommended_priority(topic: InsightTopic | None, fallback: int = 0) -> int:
        """由洞察主题优先级推导任务推荐优先级（0-100，默认 0）。"""
        if topic is None:
            return fallback
        return max(0, min(100, topic.priority_score or 0))

    def _load_topic(self, topic_id: str | None) -> InsightTopic | None:
        """按需读取关联洞察主题，不存在时抛 NotFoundError。"""
        if not topic_id:
            return None
        topic = self._insights.get_by_id(topic_id)
        if topic is None:
            raise NotFoundError(resource="洞察主题")
        return topic

    # ──────────────────────────────────────────────
    # 里程碑（RoadmapItem）
    # ──────────────────────────────────────────────

    def create_item(
        self,
        title: str,
        *,
        topic_id: str | None = None,
        owner: str | None = None,
        version: str | None = None,
    ) -> RoadmapItem:
        """创建路线图项目；关联洞察主题时校验其存在。"""
        if not title:
            raise ValidationError(detail="路线图标题不能为空")
        self._load_topic(topic_id)
        item = RoadmapItem(
            id=str(uuid.uuid4()),
            title=title,
            topic_id=topic_id,
            status="planning",
            version=version,
            owner=owner,
            due_date=None,
            progress=0,
            task_count=0,
            created_at=datetime.now(timezone.utc),
        )
        self._repo.create(item)
        self._commit()
        return item

    def get_item(self, item_id: str) -> RoadmapItem:
        """按主键读取路线图项目，不存在时抛 NotFoundError。"""
        item = self._repo.get_by_id(item_id)
        if item is None:
            raise NotFoundError(resource="路线图项目")
        return item

    def list_items(self, *, status: str | None = None) -> list[RoadmapItem]:
        """返回路线图项目（按创建时间倒序），可按状态过滤。"""
        items = sorted(
            self._repo.list_all(),  # type: ignore[arg-type]
            key=lambda item: item.created_at,
            reverse=True,
        )
        if status:
            items = [item for item in items if item.status == status]
        return items

    def update_item_status(self, item_id: str, new_status: str) -> RoadmapItem:
        """按状态机流转路线图项目状态。"""
        item = self.get_item(item_id)
        allowed = ROADMAP_STATUS_FLOW.get(item.status, set())
        if new_status not in allowed:
            raise ValidationError(
                detail=f"非法状态流转：{item.status} → {new_status}",
                errors=[
                    {
                        "field": "status",
                        "message": f"{item.status} 只能流转到 {sorted(allowed)}",
                    }
                ],
            )
        item.status = new_status
        self._commit()
        return item

    # ──────────────────────────────────────────────
    # 子任务
    # ──────────────────────────────────────────────

    def add_task(
        self,
        item_id: str,
        title: str,
        *,
        owner: str | None = None,
        priority: int = 0,
    ) -> TaskItem:
        """向路线图项目添加子任务并同步 task_count。"""
        item = self.get_item(item_id)
        if not title:
            raise ValidationError(detail="任务标题不能为空")
        task = TaskItem(
            id=str(uuid.uuid4()),
            roadmap_id=item_id,
            title=title,
            status="todo",
            owner=owner,
            priority=max(0, min(100, priority)),
            created_at=datetime.now(timezone.utc),
        )
        self._tasks.create(task)
        item.task_count = (item.task_count or 0) + 1
        self._db.flush()
        self._commit()
        return task

    def add_task_from_topic(
        self,
        item_id: str,
        title: str,
        *,
        owner: str | None = None,
    ) -> TaskItem:
        """基于关联洞察主题的推荐优先级添加任务。

        未关联主题或主题较新时按 0 处理（返回 TaskItem 供调用方复核）。
        """
        item = self.get_item(item_id)
        priority = 0
        if item.topic_id:
            topic = self._load_topic(item.topic_id)
            priority = self.compute_recommended_priority(topic)
        return self.add_task(item_id, title, owner=owner, priority=priority)

    def list_tasks(self, item_id: str) -> list[TaskItem]:
        """返回路线图项目下全部子任务（按优先级降序）。"""
        self.get_item(item_id)
        return sorted(
            [t for t in self._tasks.list_all() if t.roadmap_id == item_id],  # type: ignore[arg-type]
            key=lambda t: t.priority,
            reverse=True,
        )

    def update_task_status(self, task_id: str, new_status: str) -> TaskItem:
        """按状态机流转子任务状态。"""
        task = self._tasks.get_by_id(task_id)
        if task is None:
            raise NotFoundError(resource="任务")
        allowed = TASK_STATUS_FLOW.get(task.status, set())
        if new_status not in allowed:
            raise ValidationError(
                detail=f"非法状态流转：{task.status} → {new_status}",
                errors=[{"field": "status", "message": f"{task.status} 只能流转到 {sorted(allowed)}"}],
            )
        task.status = new_status
        self._commit()
        return task

    def recompute_progress(self, item_id: str) -> RoadmapItem:
        """按已完成任务占比重算路线图进度（0-100 取整）。"""
        item = self.get_item(item_id)
        tasks = [t for t in self._tasks.list_all() if t.roadmap_id == item_id]  # type: ignore[arg-type]
        if tasks:
            done = sum(1 for t in tasks if t.status == "done")
            item.progress = round(done / len(tasks) * 100)
        self._db.flush()
        self._commit()
        return item

    def reprioritize_tasks(self, item_id: str) -> list[TaskItem]:
        """重算任务优先级排序（按 priority 降序返回，供前端展示）。"""
        return self.list_tasks(item_id)

    # ──────────────────────────────────────────────
    # 统计
    # ──────────────────────────────────────────────

    def summary(self) -> dict[str, Any]:
        """路线图统计：项目总数 / 各状态数 / 任务总数 / 完成率。"""
        items = self.list_items()
        tasks = list(self._tasks.list_all())  # type: ignore[arg-type]
        done_tasks = sum(1 for t in tasks if t.status == "done")
        return {
            "total_items": len(items),
            "planning": sum(1 for i in items if i.status == "planning"),
            "active": sum(1 for i in items if i.status == "active"),
            "done": sum(1 for i in items if i.status == "done"),
            "total_tasks": len(tasks),
            "task_done_rate": round(done_tasks / len(tasks) * 100, 1) if tasks else 0.0,
        }

    # ──────────────────────────────────────────────
    # 回复草稿
    # ──────────────────────────────────────────────

    def save_draft(
        self,
        feedback_id: str,
        draft: str,
        *,
        excerpt: str | None = None,
        tone: str | None = None,
    ) -> ReplyDraft:
        """保存客户回复草稿（初始状态 draft）。"""
        if not draft:
            raise ValidationError(detail="草稿内容不能为空")
        reply = ReplyDraft(
            id=str(uuid.uuid4()),
            feedback_id=feedback_id,
            excerpt=excerpt,
            draft=draft,
            tone=tone,
            status="draft",
            updated_at=datetime.now(timezone.utc),
        )
        self._drafts.create(reply)
        self._commit()
        return reply

    def approve_draft(self, draft_id: str) -> ReplyDraft:
        """人工确认草稿（draft → approved）。"""
        reply = self._drafts.get_by_id(draft_id)
        if reply is None:
            raise NotFoundError(resource="回复草稿")
        reply.status = "approved"
        reply.updated_at = datetime.now(timezone.utc)
        self._commit()
        return reply