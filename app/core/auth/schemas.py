"""框架层认证 Schema。

此文件定义了用户注册、登录、Token 响应等 Pydantic 模型。
"""

import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator


class Token(BaseModel):
    """Token 模型。

    Attributes:
        access_token: API Token 字符串
        token_type: Token 类型（始终为 "bearer"）
        expires_at: Token 过期时间戳
    """

    access_token: str = Field(..., description="API Token 字符串")
    token_type: str = Field(default="bearer", description="Token 类型")
    expires_at: datetime = Field(..., description="Token 过期时间戳")


class TokenResponse(BaseModel):
    """登录端点的响应模型。

    Attributes:
        access_token: API Token 字符串
        token_type: Token 类型（始终为 "bearer"）
        expires_at: Token 过期时间
    """

    access_token: str = Field(..., description="API Token 字符串")
    token_type: str = Field(default="bearer", description="Token 类型")
    expires_at: datetime = Field(..., description="Token 过期时间")


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


class BearerTokenCreate(BaseModel):
    """创建 API Token 的请求模型。

    Attributes:
        name: Token 名称（用于识别）
        expires_in_days: Token 有效期（天数），默认 90 天
    """

    name: str = Field(..., description="Token 名称", max_length=100)
    expires_in_days: int = Field(default=90, description="Token 有效期（天数）", ge=1, le=365)


class BearerTokenResponse(BaseModel):
    """创建 API Token 的响应模型。

    Attributes:
        id: Token ID
        name: Token 名称
        token: 原始 Token 字符串（仅在创建时返回一次）
        expires_at: 过期时间
        created_at: 创建时间
    """

    id: int = Field(..., description="Token ID")
    name: str = Field(..., description="Token 名称")
    token: str = Field(..., description="原始 Token 字符串（仅在创建时返回一次）")
    expires_at: datetime = Field(..., description="过期时间")
    created_at: datetime = Field(..., description="创建时间")
