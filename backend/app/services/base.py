"""SignalFlow 后端 - Service 基类。

统一服务层的事务边界（commit / rollback）与通用类型别名。
Repository 负责数据访问，Service 负责业务规则与事务编排。
"""

from __future__ import annotations

from typing import Protocol

from sqlalchemy.orm import Session


class ServiceBase:
    """服务基类：提供统一的事务提交/回滚边界。

    业务方法在完成全部规则校验与仓储写入后调用 _commit() 落库；
    任一环节抛出业务异常时由上层（API 或编排方）负责回滚。
    """

    def __init__(self, session: Session) -> None:
        self._db = session

    def _commit(self) -> None:
        """提交当前事务。"""
        self._db.commit()

    def _rollback(self) -> None:
        """回滚当前事务。"""
        self._db.rollback()


class ReplyGenerator(Protocol):
    """AI 回复生成抽象接口（LLM Gateway 或 mock 实现）。

    Service 层只依赖该协议，不直接接触 litellm/langgraph。
    """

    def generate_reply(self, content: str) -> str:
        """根据反馈内容生成回复草稿。"""
        ...