"""用于跟踪指标和其他横切关注点的自定义中间件。"""

import time
from typing import Callable

from fastapi import Request
from jose import (
    JWTError,
    jwt,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings
from app.core.logging import (
    bind_context,
    clear_context,
)
from app.core.metrics import (
    db_connections,
    http_request_duration_seconds,
    http_requests_total,
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """用于跟踪HTTP请求指标的中间件。"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """跟踪每个请求的指标。

        Args:
            request: 传入的请求
            call_next: 下一个中间件或路由处理器

        Returns:
            Response: 来自应用程序的响应
        """
        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time

            # 记录指标
            http_requests_total.labels(method=request.method, endpoint=request.url.path, status=status_code).inc()

            http_request_duration_seconds.labels(method=request.method, endpoint=request.url.path).observe(duration)

        return response


class LoggingContextMiddleware(BaseHTTPMiddleware):
    """用于将user_id和session_id添加到日志上下文的中间件。"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """从经过身份验证的请求中提取user_id和session_id，并添加到日志上下文。

        Args:
            request: 传入的请求
            call_next: 下一个中间件或路由处理器

        Returns:
            Response: 来自应用程序的响应
        """
        try:
            # 清除之前请求的任何现有上下文
            clear_context()

            # 从Authorization header提取令牌
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

                try:
                    # 解码令牌以获取session_id（存储在"sub"声明中）
                    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                    session_id = payload.get("sub")

                    if session_id:
                        # 将session_id绑定到日志上下文
                        bind_context(session_id=session_id)

                        # 身份验证后尝试从请求状态获取user_id
                        # 如果端点使用身份验证，这将由依赖注入设置
                        # 我们将在处理请求后检查

                except JWTError:
                    # 令牌无效，但不要使请求失败 - 让auth依赖处理它
                    pass

            # 处理请求
            response = await call_next(request)

            # 请求处理后，检查用户信息是否已添加到请求状态
            if hasattr(request.state, "user_id"):
                bind_context(user_id=request.state.user_id)

            return response

        finally:
            # 请求完成后始终清除上下文，以避免泄漏到其他请求
            clear_context()
