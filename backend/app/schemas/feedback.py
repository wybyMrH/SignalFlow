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