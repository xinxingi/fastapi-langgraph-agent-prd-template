"""框架层认证依赖注入。

此文件提供 FastAPI 依赖注入函数，用于验证用户身份。
支持两种认证方式：
1. JWT Token - 用户登录后获得，用于会话管理
2. Bearer Token (API Key) - 用户主动创建，用于程序调用
"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth.jwt import get_user_id_from_token
from app.core.auth.models import BaseUser
from app.core.auth.service import auth_service
from app.core.logging import bind_context, logger
from app.utils.sanitization import sanitize_string

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> BaseUser:
    """从 Token 中获取当前用户。

    此依赖注入函数支持两种认证方式：
    1. JWT Token - 用户登录后获得的短期 token
    2. Bearer Token (API Key) - 用户创建的长期 token (sk-xxx 格式)

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

        # 判断 Token 类型并验证
        user = None

        # 如果是 API Key 格式 (sk-xxx)，使用 Bearer Token 验证
        if token.startswith("sk-"):
            user = await auth_service.verify_bearer_token(token)
            if user:
                logger.debug("authenticated_with_bearer_token", user_id=user.id)

        # 否则尝试作为 JWT Token 验证
        else:
            user_id = get_user_id_from_token(token)
            if user_id:
                user = await auth_service.get_user(user_id)
                if user and user.is_active:
                    logger.debug("authenticated_with_jwt", user_id=user.id)
                else:
                    user = None

        if user is None:
            logger.error("invalid_token", token_prefix=token[:10] + "...")
            raise HTTPException(
                status_code=401,
                detail="无效的身份验证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 将 user_id 绑定到日志上下文，用于此请求中所有后续日志
        bind_context(user_id=user.id)

        return user
    except ValueError as ve:
        logger.warning("token_validation_failed", error=str(ve))
        raise HTTPException(
            status_code=422,
            detail="无效的 token 格式",
            headers={"WWW-Authenticate": "Bearer"},
        )
