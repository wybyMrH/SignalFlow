"""SignalFlow 后端 - 统一异常体系与全局异常处理器。

设计原则：
1. 所有业务异常继承自统一的 SignalFlowException，避免裸抛 ValueError / RuntimeError。
2. 异常自动映射为结构化的 HTTP 响应 envelope（code / message / data），与前端错误处理口径一致。
3. 未捕获的未知异常返回 500 并记录 traceback，不泄露内部细节到客户端。
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class SignalFlowException(Exception):
    """业务异常基类。

    Attributes:
        status_code: 对应 HTTP 状态码
        code: 机器可读的错误码（如 NOT_FOUND）
        detail: 人类可读描述
        data: 可选附加数据（字段校验错误列表等）
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        detail: str = "服务器内部错误",
        *,
        code: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.data = data or {}
        if code:
            self.code = code


class NotFoundError(SignalFlowException):
    """资源不存在。"""

    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"

    def __init__(self, resource: str = "资源", *, detail: str | None = None, **kwargs: Any) -> None:
        msg = detail or f"{resource} 不存在"
        super().__init__(msg, **kwargs)


class ConflictError(SignalFlowException):
    """资源冲突（唯一键冲突、状态冲突等）。"""

    status_code = status.HTTP_409_CONFLICT
    code = "CONFLICT"


class ValidationError(SignalFlowException):
    """请求参数校验失败。"""

    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "VALIDATION_ERROR"

    def __init__(
        self,
        detail: str = "参数校验失败",
        *,
        errors: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(detail, data={"errors": errors or []}, **kwargs)


class PermissionDenied(SignalFlowException):
    """权限不足。"""

    status_code = status.HTTP_403_FORBIDDEN
    code = "PERMISSION_DENIED"


class Unauthorized(SignalFlowException):
    """未认证。"""

    status_code = status.HTTP_401_UNAUTHORIZED
    code = "UNAUTHORIZED"


class BadRequest(SignalFlowException):
    """通用请求错误。"""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "BAD_REQUEST"


class ServiceUnavailable(SignalFlowException):
    """依赖服务不可用（LLM 网关超时、数据库连接失败等）。"""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "SERVICE_UNAVAILABLE"


# ---------------------------------------------------------------------------
# FastAPI 全局异常处理器注册
# ---------------------------------------------------------------------------

def _make_envelope(code: str, message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"code": code, "message": message, "data": data or {}}


_HTTP_CODE_MAP: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "PERMISSION_DENIED",
    404: "NOT_FOUND",
    422: "VALIDATION_ERROR",
    500: "INTERNAL_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


def _handle_http_exception(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """统一 FastAPI/Starlette HTTPException 的响应格式为 envelope。"""
    code = _HTTP_CODE_MAP.get(exc.status_code, f"HTTP_{exc.status_code}")
    return JSONResponse(
        status_code=exc.status_code,
        content=_make_envelope(code, exc.detail),
    )


def _handle_signalflow_exception(_request: Request, exc: SignalFlowException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_make_envelope(exc.code, exc.detail, exc.data),
    )


def _handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception at %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_make_envelope(
            "INTERNAL_ERROR",
            "服务器内部错误，请稍后重试",
            {"trace_id": getattr(request.state, "trace_id", None)},
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """在 FastAPI 应用实例上注册全局异常处理器。"""
    # 优先处理 FastAPI 内置 HTTPException（404 / 422 等），统一为 envelope 格式
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(SignalFlowException, _handle_signalflow_exception)
    # 兜底：捕获任何未处理的非 HTTPException 异常
    app.add_exception_handler(Exception, _handle_generic_exception)
