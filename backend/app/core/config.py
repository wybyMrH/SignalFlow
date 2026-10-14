"""SignalFlow 后端 - 全局配置。

所有配置均通过环境变量注入（.env 或容器环境），密钥不写入代码与版本库。
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置。字段名与环境变量一一对应（大小写不敏感）。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用
    app_name: str = "SignalFlow Backend"
    app_env: Literal["development", "test", "production"] = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    # 数据库
    database_url: str = "postgresql+psycopg://signalflow:signalflow@localhost:5432/signalflow"

    # 向量检索（可选覆盖；默认与数据库同实例）
    vector_store_url: str | None = None

    # LLM 网关
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str | None = None
    llm_temperature: float = 0.2
    llm_max_tokens: int = 2048
    llm_timeout_seconds: int = 60
    llm_fallback_model: str | None = None

    # Embedding
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_api_key: str | None = None

    # 缓存
    redis_url: str = "redis://localhost:6379/0"

    # 工作流开关（骨架阶段默认关闭真实 LLM 调用）
    workflow_llm_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    """返回单例配置（FastAPI 依赖注入用）。"""
    return Settings()


settings = get_settings()