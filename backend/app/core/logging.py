"""SignalFlow 后端 - 日志组件。

统一日志格式与级别，供各层模块复用。
"""

import logging
import sys

from app.core.config import settings


def setup_logging() -> None:
    """初始化根日志器。重复调用是幂等的（logging 保证）。"""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.setLevel(level)
    # 避免重复添加 handler（多模块导入/热重载场景）
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """按模块名获取 logger。"""
    return logging.getLogger(name)