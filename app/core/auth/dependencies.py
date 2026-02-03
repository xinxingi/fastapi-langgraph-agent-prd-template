"""框架层认证依赖注入。

此文件提供 FastAPI 依赖注入函数，用于验证用户身份。
"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth.models import BaseUser
from app.core.auth.service import auth_service
from app.core.logging import bind_context, logger
from app.utils.sanitization import sanitize_string

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> BaseUser:
    """从 Bearer Token 中获取当前用户。

    此依赖注入函数验证 API Token 并返回用户对象。
    支持 API Key 格式的 Token（如 sk-xxx）。

    Args:
        credentials: 包含 Bearer Token 的 HTTP 授权凭据。

    Returns:
        BaseUser: 验证成功的用户对象。

    Raises:
        HTTPException: 如果 Token 无效、过期或用户不存在。
    """
    try:
        # 清理 Token
        token = sanitize_string(credentials.credentials)

        # 验证 Token 并获取用户
        user = await auth_service.verify_bearer_token(token)

        if user is None:
            logger.error("invalid_bearer_token", token_prefix=token[:10] + "...")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 将 user_id 绑定到日志上下文，用于此请求中所有后续日志
        bind_context(user_id=user.id)

        return user
    except ValueError as ve:
        logger.error("token_validation_failed", error=str(ve), exc_info=True)
        raise HTTPException(
            status_code=422,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
