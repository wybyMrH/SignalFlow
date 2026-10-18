"""SignalFlow 后端 - 系统设置接口。

返回系统设置视图（SettingsView 契约）：
mock 模式标记、渠道接入状态、AI 与认证说明、API 配置、服务器配置、
邮件配置、AI 气泡主题、全局模型参数、Agent 角色提示词。骨架阶段数据以
SettingsService 的 KV 配置与渠道表为准，未配置字段给出默认说明。
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from app.core.database import get_db
from app.services.agents import AgentService
from app.services.settings import SettingsService
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()


def _service(db: Session = Depends(get_db)) -> SettingsService:
    return SettingsService(db)


def _agent_service(db: Session = Depends(get_db)) -> AgentService:
    return AgentService(db)


# ──────────────────────────────────────────────
# Pydantic 更新模型
# ──────────────────────────────────────────────


class LLMConfigUpdate(BaseModel):
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    timeout_seconds: int | None = None


class EmailConfigUpdate(BaseModel):
    enabled: bool | None = None
    smtp_server: str | None = None
    smtp_port: int | None = None
    sender: str | None = None
    password: str | None = None


class AppearanceConfigUpdate(BaseModel):
    ai_bubble_theme: str | None = None


class GlobalModelParamsUpdate(BaseModel):
    context_window: int | None = None
    tone: str | None = None


class ServerConfigUpdate(BaseModel):
    log_level: str | None = None


class NotesConfigUpdate(BaseModel):
    ai_note: str | None = None
    auth_note: str | None = None


class ChannelToggleResult(BaseModel):
    code: str = "SUCCESS"
    message: str
    data: dict


# ──────────────────────────────────────────────
# GET 系统设置视图
# ──────────────────────────────────────────────


@router.get("")
def get_settings(
    service: SettingsService = Depends(_service),
    agent_service: AgentService = Depends(_agent_service),
) -> dict:
    """系统设置视图：返回全部配置分区。"""
    channels = []
    for cfg in service.list_channels():
        channels.append(
            {
                "key": cfg.key,
                "label": cfg.label,
                "enabled": cfg.enabled,
                "connected": cfg.connected,
                "last_sync": cfg.last_sync.isoformat() if cfg.last_sync else None,
                "incoming": cfg.incoming or 0,
                "note": cfg.note or "",
            }
        )

    # Agent 角色提示词（从 agents 表读取）
    agent_prompts = []
    for agent in agent_service.list():
        agent_prompts.append(
            {
                "id": agent.id,
                "name": agent.name,
                "category": agent.category,
                "scenario": agent.scenario or "",
                "enabled": agent.enabled,
            }
        )

    # LLM 配置：KV 覆盖 > 环境变量 > 默认值
    llm_api_key = service.get_config_or(
        "llm_api_key", os.getenv("LLM_API_KEY", "")
    )

    # 邮件配置
    email_password = service.get_config_or(
        "email_password", os.getenv("SMTP_PASSWORD", "")
    )

    return {
        "mock_mode": service.get_config_or("mock_mode", "true").lower() == "true",
        "channels": channels,
        "llm": {
            "provider": service.get_config_or(
                "llm_provider", os.getenv("LLM_PROVIDER", "openai")
            ),
            "model": service.get_config_or(
                "llm_model", os.getenv("LLM_MODEL", "gpt-4o-mini")
            ),
            "api_key_mask": "••••••" + llm_api_key[-4:] if len(llm_api_key) > 4 else "",
            "temperature": float(
                service.get_config_or(
                    "llm_temperature", os.getenv("LLM_TEMPERATURE", "0.2")
                )
            ),
            "max_tokens": int(
                service.get_config_or(
                    "llm_max_tokens", os.getenv("LLM_MAX_TOKENS", "2048")
                )
            ),
            "timeout_seconds": int(
                service.get_config_or(
                    "llm_timeout_seconds", os.getenv("LLM_TIMEOUT_SECONDS", "60")
                )
            ),
        },
        "email": {
            "enabled": service.get_config_or("email_enabled", "false").lower()
            == "true",
            "smtp_server": service.get_config_or(
                "email_smtp_server", os.getenv("SMTP_SERVER", "")
            ),
            "smtp_port": int(
                service.get_config_or(
                    "email_smtp_port", os.getenv("SMTP_PORT", "587") or "587"
                )
            ),
            "sender": service.get_config_or(
                "email_sender", os.getenv("SMTP_SENDER", "")
            ),
            "password_mask": "••••••" if email_password else "",
        },
        "appearance": {
            "ai_bubble_theme": service.get_config_or("ai_bubble_theme", "blue"),
        },
        "global_model_params": {
            "context_window": int(service.get_config_or("context_window", "4096")),
            "tone": service.get_config_or("model_tone", "professional"),
        },
        "server": {
            "app_env": os.getenv("APP_ENV", "development"),
            "app_host": os.getenv("APP_HOST", "0.0.0.0"),
            "app_port": int(os.getenv("APP_PORT", "8000")),
            "log_level": service.get_config_or(
                "log_level", os.getenv("LOG_LEVEL", "INFO")
            ),
        },
        "agent_prompts": agent_prompts,
        "ai_note": service.get_config_or(
            "ai_note",
            "AI 工作流已就绪（骨架阶段使用规则引擎，接入 LLM 网关后切换真实输出）。",
        ),
        "auth_note": service.get_config_or(
            "auth_note", "统一身份认证接入位已预留，本阶段不启用登录。"
        ),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


# ──────────────────────────────────────────────
# PUT 配置更新
# ──────────────────────────────────────────────


@router.put("/llm")
def update_llm_config(
    payload: LLMConfigUpdate,
    service: SettingsService = Depends(_service),
) -> dict:
    """更新 LLM / API 配置。"""
    if payload.provider is not None:
        service.set_config("llm_provider", payload.provider)
    if payload.model is not None:
        service.set_config("llm_model", payload.model)
    if payload.api_key is not None and payload.api_key.strip():
        service.set_config("llm_api_key", payload.api_key)
    if payload.temperature is not None:
        service.set_config("llm_temperature", str(payload.temperature))
    if payload.max_tokens is not None:
        service.set_config("llm_max_tokens", str(payload.max_tokens))
    if payload.timeout_seconds is not None:
        service.set_config("llm_timeout_seconds", str(payload.timeout_seconds))
    return {"code": "SUCCESS", "message": "LLM 配置已更新"}


@router.put("/email")
def update_email_config(
    payload: EmailConfigUpdate,
    service: SettingsService = Depends(_service),
) -> dict:
    """更新邮件提醒配置。"""
    if payload.enabled is not None:
        service.set_config("email_enabled", "true" if payload.enabled else "false")
    if payload.smtp_server is not None:
        service.set_config("email_smtp_server", payload.smtp_server)
    if payload.smtp_port is not None:
        service.set_config("email_smtp_port", str(payload.smtp_port))
    if payload.sender is not None:
        service.set_config("email_sender", payload.sender)
    if payload.password is not None and payload.password.strip():
        service.set_config("email_password", payload.password)
    return {"code": "SUCCESS", "message": "邮件配置已更新"}


@router.put("/appearance")
def update_appearance_config(
    payload: AppearanceConfigUpdate,
    service: SettingsService = Depends(_service),
) -> dict:
    """更新外观 / AI 气泡主题。"""
    if payload.ai_bubble_theme is not None:
        service.set_config("ai_bubble_theme", payload.ai_bubble_theme)
    return {"code": "SUCCESS", "message": "外观配置已更新"}


@router.put("/global-model-params")
def update_global_model_params(
    payload: GlobalModelParamsUpdate,
    service: SettingsService = Depends(_service),
) -> dict:
    """更新全局模型微调参数。"""
    if payload.context_window is not None:
        service.set_config("context_window", str(payload.context_window))
    if payload.tone is not None:
        service.set_config("model_tone", payload.tone)
    return {"code": "SUCCESS", "message": "全局模型参数已更新"}


@router.put("/server")
def update_server_config(
    payload: ServerConfigUpdate,
    service: SettingsService = Depends(_service),
) -> dict:
    """更新服务器运行参数（启动级参数保持环境变量，仅支持运行时可调项）。"""
    if payload.log_level is not None:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        level = payload.log_level.strip().upper()
        if level not in valid_levels:
            return {
                "code": "INVALID_ARGUMENT",
                "message": f"日志级别仅支持 {'、'.join(sorted(valid_levels))}",
            }
        service.set_config("log_level", level)
    return {"code": "SUCCESS", "message": "服务器配置已更新"}


@router.put("/notes")
def update_notes_config(
    payload: NotesConfigUpdate,
    service: SettingsService = Depends(_service),
) -> dict:
    """更新数据源与权限说明文案（AI 洞察 / 身份认证）。"""
    if payload.ai_note is not None:
        service.set_config("ai_note", payload.ai_note)
    if payload.auth_note is not None:
        service.set_config("auth_note", payload.auth_note)
    return {"code": "SUCCESS", "message": "数据源与权限说明已更新"}


@router.put("/channels/{key}/toggle")
def toggle_channel(
    key: str,
    service: SettingsService = Depends(_service),
) -> dict:
    """切换渠道启用 / 停用状态。"""
    channel = service.toggle_channel(key)
    return {
        "code": "SUCCESS",
        "message": f"渠道 {channel.label} 已{'启用' if channel.enabled else '停用'}",
        "data": {
            "key": channel.key,
            "enabled": channel.enabled,
            "connected": channel.connected,
        },
    }
