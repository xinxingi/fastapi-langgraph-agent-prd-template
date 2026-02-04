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
        expires_at: Token 过期时间
    """

    access_token: str = Field(..., description="API Token 字符串")
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
    """用户注册的响应模型。

    Attributes:
        id: 用户的ID
        email: 用户的电子邮件地址
        message: 成功消息
    """

    id: int = Field(..., description="用户的ID")
    email: str = Field(..., description="用户的电子邮件地址")
    message: str = Field(default="User registered successfully", description="成功消息")


class ApiKeyCreate(BaseModel):
    """创建 API Key 的请求模型。

    注意：API Key 使用 Bearer 认证方案传递（Authorization: Bearer sk-xxx）

    Attributes:
        name: API Key 名称（用于识别）
        expires_in_days: API Key 有效期（天数），默认 90 天，最长可设置到 2099 年
    """

    name: str = Field(..., description="API Key 名称", max_length=100)
    expires_in_days: int = Field(
        default=90, description="API Key 有效期（天数），最长可设置到 2099 年", ge=1, le=27000
    )

    @field_validator("expires_in_days")
    @classmethod
    def validate_expiry_date(cls, v: int) -> int:
        """验证过期时间不超过 2099 年。

        Args:
            v: 要验证的天数

        Returns:
            int: 验证后的天数

        Raises:
            ValueError: 如果过期日期超过 2099 年
        """
        from datetime import datetime, timedelta, UTC

        max_date = datetime(2099, 12, 31, tzinfo=UTC)
        future_date = datetime.now(UTC) + timedelta(days=v)

        if future_date > max_date:
            raise ValueError(f"过期时间不能超过 2099 年 12 月 31 日")

        return v


class ApiKeyUpdate(BaseModel):
    """更新 API Key 的请求模型。

    Attributes:
        expires_in_days: 新的有效期（天数），最长可设置到 2099 年
    """

    expires_in_days: int = Field(..., description="新的有效期（天数），最长可设置到 2099 年", ge=1, le=27000)

    @field_validator("expires_in_days")
    @classmethod
    def validate_expiry_date(cls, v: int) -> int:
        """验证过期时间不超过 2099 年。

        Args:
            v: 要验证的天数

        Returns:
            int: 验证后的天数

        Raises:
            ValueError: 如果过期日期超过 2099 年
        """
        from datetime import datetime, timedelta, UTC

        max_date = datetime(2099, 12, 31, tzinfo=UTC)
        future_date = datetime.now(UTC) + timedelta(days=v)

        if future_date > max_date:
            raise ValueError(f"过期时间不能超过 2099 年 12 月 31 日")

        return v


class ApiKeyResponse(BaseModel):
    """创建 API Key 的响应模型。

    Attributes:
        id: API Key ID
        name: API Key 名称
        token: 原始 API Key 字符串（sk-xxx 格式，仅在创建时返回一次）
        expires_at: 过期时间
        created_at: 创建时间
    """

    id: int = Field(..., description="API Key ID")
    name: str = Field(..., description="API Key 名称")
    token: str = Field(..., description="原始 API Key 字符串（sk-xxx 格式，仅在创建时返回一次）")
    expires_at: datetime = Field(..., description="过期时间")
    created_at: datetime = Field(..., description="创建时间")


class ApiKeyListItem(BaseModel):
    """API Key 列表项模型（不包含 token 字段）。

    Attributes:
        id: API Key ID
        name: API Key 名称
        expires_at: 过期时间
        created_at: 创建时间
        revoked: 是否已撤销
        last_used_at: 最后使用时间（如果从未使用过则为 None）
        bound_projects_count: 绑定的项目数量
    """

    id: int = Field(..., description="API Key ID")
    name: str = Field(..., description="API Key 名称")
    expires_at: datetime = Field(..., description="过期时间")
    created_at: datetime = Field(..., description="创建时间")
    revoked: bool = Field(..., description="是否已撤销")
    last_used_at: datetime | None = Field(default=None, description="最后使用时间（如果从未使用过则为 None）")
    bound_projects_count: int = Field(default=0, description="绑定的项目数量")


class ApiKeyListResponse(BaseModel):
    """API Key 列表的分页响应模型。

    Attributes:
        items: API Key 列表
        total: 总记录数
        skip: 跳过的记录数
        limit: 返回的最大记录数
    """

    items: list[ApiKeyListItem] = Field(..., description="API Key 列表")
    total: int = Field(..., description="总记录数")
    skip: int = Field(..., description="跳过的记录数")
    limit: int = Field(..., description="返回的最大记录数")


# 保持向后兼容的别名
BearerTokenCreate = ApiKeyCreate
BearerTokenResponse = ApiKeyResponse


class ProjectCreate(BaseModel):
    """创建项目的请求模型。

    Attributes:
        name: 项目名称（唯一）
        description: 项目描述
    """

    name: str = Field(..., description="项目名称", max_length=100)
    description: str | None = Field(default=None, description="项目描述", max_length=500)


class ProjectUpdate(BaseModel):
    """更新项目的请求模型。

    Attributes:
        name: 项目名称（唯一）
        description: 项目描述
        is_active: 项目是否激活
    """

    name: str | None = Field(default=None, description="项目名称", max_length=100)
    description: str | None = Field(default=None, description="项目描述", max_length=500)
    is_active: bool | None = Field(default=None, description="项目是否激活")


class ProjectResponse(BaseModel):
    """项目响应模型。

    Attributes:
        id: 项目ID
        name: 项目名称
        description: 项目描述
        is_active: 项目是否激活
        created_at: 创建时间
        updated_at: 更新时间
    """

    id: int = Field(..., description="项目ID")
    name: str = Field(..., description="项目名称")
    description: str | None = Field(default=None, description="项目描述")
    is_active: bool = Field(..., description="项目是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ProjectListResponse(BaseModel):
    """项目列表的分页响应模型。

    Attributes:
        items: 项目列表
        total: 总记录数
        skip: 跳过的记录数
        limit: 返回的最大记录数
    """

    items: list[ProjectResponse] = Field(..., description="项目列表")
    total: int = Field(..., description="总记录数")
    skip: int = Field(..., description="跳过的记录数")
    limit: int = Field(..., description="返回的最大记录数")


class AssignProjectToUser(BaseModel):
    """为用户分配项目的请求模型。

    Attributes:
        user_id: 用户ID
        project_id: 项目ID
        role: 用户在项目中的角色
    """

    user_id: int = Field(..., description="用户ID")
    project_id: int = Field(..., description="项目ID")
    role: str = Field(default="member", description="用户在项目中的角色", max_length=50)


class AssignProjectToApiKey(BaseModel):
    """为 API Key 分配项目的请求模型。

    Attributes:
        api_key_id: API Key ID
        project_id: 项目ID
    """

    api_key_id: int = Field(..., description="API Key ID")
    project_id: int = Field(..., description="项目ID")


class UserProjectResponse(BaseModel):
    """用户-项目关联响应模型。

    Attributes:
        id: 关联ID
        user_id: 用户ID
        project_id: 项目ID
        role: 用户在项目中的角色
        created_at: 创建时间
        project: 项目信息
    """

    id: int = Field(..., description="关联ID")
    user_id: int = Field(..., description="用户ID")
    project_id: int = Field(..., description="项目ID")
    role: str = Field(..., description="用户在项目中的角色")
    created_at: datetime = Field(..., description="创建时间")
    project: ProjectResponse | None = Field(default=None, description="项目信息")


class ApiKeyProjectResponse(BaseModel):
    """API Key-项目关联响应模型。

    Attributes:
        id: 关联ID
        api_key_id: API Key ID
        project_id: 项目ID
        created_at: 创建时间
        project: 项目信息
    """

    id: int = Field(..., description="关联ID")
    api_key_id: int = Field(..., description="API Key ID")
    project_id: int = Field(..., description="项目ID")
    created_at: datetime = Field(..., description="创建时间")
    project: ProjectResponse | None = Field(default=None, description="项目信息")
