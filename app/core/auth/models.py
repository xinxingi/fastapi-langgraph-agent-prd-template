"""框架层数据库模型。

此文件定义了框架层的用户和 Bearer Token 模型。
表命名遵循 bs_ 前缀规范。
"""

from datetime import datetime, timedelta, UTC
from typing import Optional, List, TYPE_CHECKING

import bcrypt
from sqlmodel import Field, Relationship

from app.core.models.base import BaseModel

if TYPE_CHECKING:
    pass


class BaseUser(BaseModel, table=True):
    """框架层用户模型。

    对应数据库表: bs_users

    Attributes:
        id: 用户主键
        email: 用户邮箱（唯一）
        hashed_password: bcrypt 哈希后的密码
        is_active: 用户是否激活
        is_superuser: 是否为超级管理员
        created_at: 创建时间（继承自 BaseModel）
        updated_at: 更新时间
        bearer_tokens: 用户的 API Token 列表（关系字段）
    """

    __tablename__ = "bs_users"

    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"comment": "用户ID"})
    email: str = Field(unique=True, index=True, max_length=255, sa_column_kwargs={"comment": "用户邮箱"})
    hashed_password: str = Field(max_length=255, sa_column_kwargs={"comment": "bcrypt哈希后的密码"})
    is_active: bool = Field(default=True, sa_column_kwargs={"comment": "用户是否激活"})
    is_superuser: bool = Field(default=False, sa_column_kwargs={"comment": "是否为超级管理员"})
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column_kwargs={"comment": "更新时间"})

    # 关系
    bearer_tokens: List["BearerToken"] = Relationship(back_populates="user", cascade_delete=True)

    def verify_password(self, password: str) -> bool:
        """验证提供的密码是否与哈希值匹配。

        Args:
            password: 明文密码

        Returns:
            bool: 密码是否匹配
        """
        return bcrypt.checkpw(password.encode("utf-8"), self.hashed_password.encode("utf-8"))

    @staticmethod
    def hash_password(password: str) -> str:
        """使用 bcrypt 哈希密码。

        Args:
            password: 明文密码

        Returns:
            str: 哈希后的密码
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


class BearerToken(BaseModel, table=True):
    """API Bearer Token 模型。

    对应数据库表: bs_bearer_tokens
    存储用户的 API Key（如 sk-xxx 格式），用于长期访问认证。

    Attributes:
        id: Token 主键
        user_id: 所属用户ID（外键）
        name: Token 名称（用于识别不同的 Token）
        token_hash: Token 的 SHA256 哈希值（唯一）
        expires_at: 过期时间
        revoked: 是否已撤销
        created_at: 创建时间（继承自 BaseModel）
        user: 所属用户（关系字段）
    """

    __tablename__ = "bs_bearer_tokens"

    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"comment": "Token ID"})
    user_id: int = Field(foreign_key="bs_users.id", sa_column_kwargs={"comment": "所属用户ID"})
    name: Optional[str] = Field(default=None, max_length=100, sa_column_kwargs={"comment": "Token名称"})
    token_hash: str = Field(
        unique=True, index=True, max_length=255, sa_column_kwargs={"comment": "Token的SHA256哈希值"}
    )
    expires_at: datetime = Field(sa_column_kwargs={"comment": "过期时间"})
    revoked: bool = Field(default=False, sa_column_kwargs={"comment": "是否已撤销"})

    # 关系
    user: BaseUser = Relationship(back_populates="bearer_tokens")

    @staticmethod
    def hash_token(token: str) -> str:
        """哈希 API Token。

        Args:
            token: 原始 Token 字符串

        Returns:
            str: SHA256 哈希值
        """
        import hashlib

        return hashlib.sha256(token.encode()).hexdigest()

    def is_expired(self) -> bool:
        """检查 Token 是否已过期。

        Returns:
            bool: Token 是否过期
        """
        return datetime.now(UTC) > self.expires_at.replace(tzinfo=UTC)

    def is_valid(self) -> bool:
        """检查 Token 是否有效（未过期且未撤销）。

        Returns:
            bool: Token 是否有效
        """
        return not self.revoked and not self.is_expired()
