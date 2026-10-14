"""SignalFlow 后端 - 测试公共夹具。

骨架阶段保持轻量：后续切片引入真实数据库时，
再切换到独立测试库（TEST_DATABASE_URL）与事务回滚式 fixtures。
"""

import pytest


@pytest.fixture
def app_settings():
    """返回当前应用配置实例，供测试断言使用。"""
    from app.core.config import get_settings

    return get_settings()