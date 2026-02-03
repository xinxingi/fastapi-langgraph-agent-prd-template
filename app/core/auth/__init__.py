"""框架层认证模块。

此模块提供基于用户和 Bearer Token (API Key) 的认证机制。
"""

from app.core.auth.dependencies import get_current_user
from app.core.auth.models import (
    BearerToken,
    BaseUser,
)
from app.core.auth.schemas import (
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.core.auth.service import AuthService

__all__ = [
    "get_current_user",
    "BearerToken",
    "BaseUser",
    "TokenResponse",
    "UserCreate",
    "UserResponse",
    "AuthService",
]
