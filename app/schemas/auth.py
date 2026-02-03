"""此文件包含应用程序的认证schema。"""

import re
from datetime import datetime

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
)


class Token(BaseModel):
    """认证的Token模型。

    Attributes:
        access_token: JWT访问令牌。
        token_type: 令牌类型（始终为"bearer"）。
        expires_at: 令牌过期时间戳。
    """

    access_token: str = Field(..., description="JWT访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_at: datetime = Field(..., description="令牌过期时间戳")


class TokenResponse(BaseModel):
    """登录端点的响应模型。

    Attributes:
        access_token: JWT访问令牌
        token_type: 令牌类型（始终为"bearer"）
        expires_at: 令牌过期时间
    """

    access_token: str = Field(..., description="JWT访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_at: datetime = Field(..., description="令牌过期时间")


class UserCreate(BaseModel):
    """用户注册的请求模型。

    Attributes:
        email: 用户的电子邮件地址
        password: 用户的密码
    """

    email: EmailStr = Field(..., description="用户的电子邮件地址")
    password: SecretStr = Field(..., description="用户的密码", min_length=8, max_length=64)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: SecretStr) -> SecretStr:
        """验证密码强度。

        Args:
            v: 要验证的密码

        Returns:
            SecretStr: 验证后的密码

        Raises:
            ValueError: 如果密码强度不够
        """
        password = v.get_secret_value()

        # 检查常见的密码要求
        if len(password) < 8:
            raise ValueError("密码长度至少为8个字符")

        if not re.search(r"[A-Z]", password):
            raise ValueError("密码必须包含至少一个大写字母")

        if not re.search(r"[a-z]", password):
            raise ValueError("密码必须包含至少一个小写字母")

        if not re.search(r"[0-9]", password):
            raise ValueError("密码必须包含至少一个数字")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("密码必须包含至少一个特殊字符")

        return v


class UserResponse(BaseModel):
    """用户操作的响应模型。

    Attributes:
        id: 用户的ID
        email: 用户的电子邮件地址
        token: 认证令牌
    """

    id: int = Field(..., description="用户的ID")
    email: str = Field(..., description="用户的电子邮件地址")
    token: Token = Field(..., description="认证令牌")


class SessionResponse(BaseModel):
    """会话创建的响应模型。

    Attributes:
        session_id: 聊天会话的唯一标识符
        name: 会话名称（默认为空字符串）
        token: 会话的认证令牌
    """

    session_id: str = Field(..., description="聊天会话的唯一标识符")
    name: str = Field(default="", description="会话名称", max_length=100)
    token: Token = Field(..., description="会话的认证令牌")

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        """清理会话名称。

        Args:
            v: 要清理的名称

        Returns:
            str: 清理后的名称
        """
        # 移除任何可能有害的字符
        sanitized = re.sub(r'[<>{}[\]()\'"`]', "", v)
        return sanitized
