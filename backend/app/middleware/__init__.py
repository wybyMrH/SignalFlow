"""SignalFlow 后端 - HTTP 中间件包。

按 FastAPI `app.add_middleware` 注册顺序：
1. CORS（最外层，跨域）
2. RequestLogMiddleware（请求日志与 trace_id 注入）
3. （后续切片可追加：RateLimitMiddleware / AuthMiddleware / CacheMiddleware）
"""
