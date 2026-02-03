"""JWT Token 管理工具。

提供 JWT Token 的创建、验证和解析功能。
"""

from datetime import datetime, timedelta, UTC
from typing import Optional

from jose import JWTError, jwt

from app.core.config import settings
from app.core.logging import logger


def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT Access Token。

    Args:
        user_id: 用户ID
        expires_delta: Token 有效期，如果为 None 则使用配置的默认值

    Returns:
        str: JWT Token 字符串
    """
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(days=settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode = {"sub": str(user_id), "exp": expire, "iat": datetime.now(UTC), "type": "access"}

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    logger.debug("jwt_token_created", user_id=user_id, expires_at=expire.isoformat())

    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """验证 JWT Token 并返回 payload。

    Args:
        token: JWT Token 字符串

    Returns:
        Optional[dict]: Token payload，如果验证失败则返回 None
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        # 检查 token 类型
        if payload.get("type") != "access":
            logger.warning("invalid_token_type", token_type=payload.get("type"))
            return None

        return payload

    except JWTError as e:
        logger.warning("jwt_verification_failed", error=str(e))
        return None


def get_user_id_from_token(token: str) -> Optional[int]:
    """从 JWT Token 中提取用户 ID。

    Args:
        token: JWT Token 字符串

    Returns:
        Optional[int]: 用户 ID，如果验证失败则返回 None
    """
    payload = verify_token(token)
    if not payload:
        return None

    try:
        user_id = int(payload.get("sub"))
        return user_id
    except (ValueError, TypeError):
        logger.warning("invalid_user_id_in_token", sub=payload.get("sub"))
        return None
