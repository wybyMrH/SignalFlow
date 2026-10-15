"""SignalFlow 后端 - LangGraph Checkpoint 持久化到 PostgreSQL。

使用 ``langgraph-checkpoint-postgres`` 提供的 PostgresSaver，
将工作流执行状态持久化到 PostgreSQL，支持中断恢复。

连接池基于 psycopg（同步）构建，与 SQLAlchemy 连接独立管理，
避免 ORM session 与 LangGraph checkpoint 互相干扰。

注意：为便于在无法使用后台线程调度池的环境中测试，get_checkpointer /
setup_checkpoint 支持注入外部 :class:`psycopg.Connection`（绕过 ConnectionPool）。
"""

from __future__ import annotations

import re
from typing import Union

import psycopg
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# PostgresSaver 可接受的连接类型：普通连接或连接池
PoolConnection = Union["psycopg.Connection", ConnectionPool]

# 标记"连接对象无 autocommit 属性"（如连接池项）
_sentinel = object()

_pool: ConnectionPool | None = None


def _raw_conninfo() -> str:
    """将 SQLAlchemy URI 转换为 psycopg 原生连接字符串。"""
    url = settings.database_url
    # 去掉 SQLAlchemy driver 前缀（如 postgresql+psycopg）
    raw = re.sub(r"^postgresql\+[^:/]+", "postgresql", url)
    return raw


def get_pool() -> ConnectionPool:
    """返回（或创建）全局 psycopg 连接池。"""
    global _pool
    if _pool is None:
        conninfo = _raw_conninfo()
        logger.info("Creating LangGraph checkpoint connection pool: %s", conninfo.split("@")[-1])
        _pool = ConnectionPool(conninfo=conninfo, max_size=10)
    return _pool


def get_checkpointer(conn: PoolConnection | None = None) -> PostgresSaver:
    """获取基于 PostgreSQL 的 LangGraph CheckpointSaver。

    用法示例：
    ::

        graph = build_analysis_graph()
        checkpointer = get_checkpointer()
        compiled = graph.compile(checkpointer=checkpointer)

    参数：
        conn: 可选的外部连接/连接池；不传时使用内部全局 psycopg 连接池。
              传入普通 :class:`psycopg.Connection` 可绕过连接池（便于测试）。
    """
    if conn is None:
        return PostgresSaver(conn=get_pool())
    return PostgresSaver(conn=conn)


def setup_checkpoint(conn: PoolConnection | None = None) -> None:
    """初始化 checkpoint 表（幂等，应用启动时调用一次）。

    PostgresSaver.setup() 内部使用 ``CREATE INDEX CONCURRENTLY``，该语句
    不能在事务块内执行，因此这里对传入连接启用 autocommit 后执行，
    结束后恢复原事务状态（普通 psycopg 连接才会被修改；连接池项在归还
    时由池自行管理）。

    参数：
        conn: 可选的外部连接/连接池；不传时从内部全局连接池取连接。
    """

    def _apply(target_conn) -> None:
        autocommit = getattr(target_conn, "autocommit", _sentinel)
        try:
            if autocommit is not _sentinel:
                target_conn.autocommit = True
            PostgresSaver(conn=target_conn).setup()
        finally:
            if autocommit is not _sentinel:
                target_conn.autocommit = autocommit

    if conn is not None:
        _apply(conn)
        logger.info("LangGraph checkpoint tables initialized (injected connection)")
        return
    pool = get_pool()
    with pool.connection() as pool_conn:
        _apply(pool_conn)
    logger.info("LangGraph checkpoint tables initialized")