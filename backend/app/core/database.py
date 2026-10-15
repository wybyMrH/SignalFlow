"""SignalFlow 后端 - 数据库与会话管理。

统一创建 SQLAlchemy engine、Session 工厂与依赖注入依赖。
骨架阶段提供基础设施，真实业务表在后续切片中通过 Alembic 迁移创建。
"""

from collections.abc import Generator

from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """ORM 声明式基类，所有模型继承此类。"""


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=settings.app_debug,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：提供请求级数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()