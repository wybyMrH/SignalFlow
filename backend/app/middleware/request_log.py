"""SignalFlow 后端 - 请求日志与 Trace ID 中间件。

为每个 HTTP 请求生成唯一 trace_id，记录请求方法、路径、状态码、耗时，
并注入到 response header（X-Request-Id）与日志上下文，便于全链路追踪。
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("signalflow.request")


class RequestLogMiddleware(BaseHTTPMiddleware):
    """请求日志中间件。

    注册方式：
        app.add_middleware(RequestLogMiddleware)
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            # 记录异常并继续上抛，由全局异常处理器接管
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "[%s] %s %s -> EXC  %.2fms  %s",
                trace_id,
                request.method,
                request.url.path,
                duration_ms,
                exc.__class__.__name__,
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        status_code = response.status_code
        logger.info(
            "[%s] %s %s -> %d  %.2fms",
            trace_id,
            request.method,
            request.url.path,
            status_code,
            duration_ms,
        )

        response.headers["X-Request-Id"] = trace_id
        return response
