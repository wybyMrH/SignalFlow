"""SignalFlow 后端 - 系统设置接口。

返回系统设置视图（SettingsView 契约）：
mock 模式标记、渠道接入状态、AI 与认证说明。骨架阶段数据以
SettingsService 的 KV 配置与渠道表为准，未配置字段给出默认说明。
"""

from datetime import datetime, timezone

from app.core.database import get_db
from app.services.settings import SettingsService
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


def _service(db: Session = Depends(get_db)) -> SettingsService:
    return SettingsService(db)


@router.get("")
def get_settings(service=Depends(_service)) -> dict:
    """系统设置视图。"""
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
    return {
        "mock_mode": service.get_config_or("mock_mode", "true").lower() == "true",
        "channels": channels,
        "ai_note": service.get_config_or(
            "ai_note", "AI 工作流已就绪（骨架阶段使用规则引擎，接入 LLM 网关后切换真实输出）。"
        ),
        "auth_note": service.get_config_or(
            "auth_note", "政务版统一身份认证接入位已预留，本阶段不启用登录。"
        ),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }