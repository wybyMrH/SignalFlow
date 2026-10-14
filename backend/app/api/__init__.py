"""SignalFlow 后端 - API 路由层。

Router 只做参数校验与 HTTP 适配，业务逻辑一律委托给 service 层。
"""

from app.api.v1.router import api_router

__all__ = ["api_router"]