"""SignalFlow 后端 - 反馈相关的 Pydantic Schema。

FeedbackRead 为对外契约；字段变化需同步更新前端 types 与 API 文档。
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    """创建反馈的请求体。"""

    source: str = Field(default="manual", max_length=64)
    source_ref: str | None = Field(default=None, max_length=128)
    content: str = Field(min_length=1, max_length=20000)
    author: str | None = Field(default=None, max_length=128)


class FeedbackRead(BaseModel):
    """反馈的对外只读表示。"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    source: str
    source_ref: str | None
    content: str
    author: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class FeedbackView(FeedbackRead):
    """反馈视图：基础实体 + 前端展示扩展字段。

    骨架阶段扩展字段尚未落库，默认返回 None/0，
    真实后端就绪后由关联接口组装或模型回填。
    """

    topic_id: str | None = None
    topic_title: str | None = None
    priority: int = 0
    sentiment: str | None = None
    reviewer: str | None = None
    reply_content: str | None = None
    replied_at: datetime | None = None
    # 业务编号（展示用短编号，如 F1048）：与前端 mock 数据 id 口径一致，
    # 使 8088(mock) 与 5199(真后端) 的列表/详情展示完全相同；运行时新建反馈可为空。
    code: str | None = None


class FeedbackStats(BaseModel):
    """反馈状态统计。"""

    total: int = 0
    new: int = 0
    analyzing: int = 0
    ai_reviewing: int = 0
    ai_replied: int = 0
    resolved: int = 0
    replied: int = 0
    closed: int = 0
    high_priority: int = 0


class FeedbackStatusUpdate(BaseModel):
    """反馈状态流转请求体。"""

    status: str
    reviewer: str | None = None
    reply_content: str | None = None
