"""框架层认证服务。

此文件提供用户注册、登录、Token 管理等服务。
"""

import secrets
from datetime import datetime, timedelta, UTC
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool
from sqlmodel import Session, create_engine, select

from app.core.auth.models import BaseUser, ApiKey
from app.core.auth.schemas import Token
from app.core.config import settings
from app.core.logging import logger


class AuthService:
    """框架层认证服务类。

    该类处理用户、Token 的所有数据库操作。
    使用 SQLModel 进行 ORM 操作并维护连接池。
    """

    def __init__(self):
        """初始化认证服务，创建数据库引擎和表。"""
        try:
            # 配置数据库连接池
            pool_size = settings.POSTGRES_POOL_SIZE
            max_overflow = settings.POSTGRES_MAX_OVERFLOW

            connection_url = (
                f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
                f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
            )

            self.engine = create_engine(
                connection_url,
                pool_pre_ping=True,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=30,
                pool_recycle=1800,
            )

            # 创建表（仅当它们不存在时）
            from sqlmodel import SQLModel

            SQLModel.metadata.create_all(self.engine)

            logger.info(
                "auth_service_initialized",
                pool_size=pool_size,
                max_overflow=max_overflow,
            )
        except SQLAlchemyError as e:
            logger.error("auth_service_initialization_error", error=str(e))
            raise

    async def create_user(self, email: str, password: str) -> BaseUser:
        """创建新用户。

        Args:
            email: 用户的邮箱地址
            password: 哈希密码

        Returns:
            BaseUser: 创建的用户
        """
        with Session(self.engine) as session:
            user = BaseUser(email=email, hashed_password=password)
            session.add(user)
            session.commit()
            session.refresh(user)
            logger.info("user_created", email=email, user_id=user.id)
            return user

    async def get_user(self, user_id: int) -> Optional[BaseUser]:
        """通过 ID 获取用户。

        Args:
            user_id: 要检索的用户 ID

        Returns:
            Optional[BaseUser]: 如果找到则返回用户，否则返回 None
        """
        with Session(self.engine) as session:
            user = session.get(BaseUser, user_id)
            return user

    async def get_user_by_email(self, email: str) -> Optional[BaseUser]:
        """通过邮箱获取用户。

        Args:
            email: 要检索的用户邮箱

        Returns:
            Optional[BaseUser]: 如果找到则返回用户，否则返回 None
        """
        with Session(self.engine) as session:
            statement = select(BaseUser).where(BaseUser.email == email)
            user = session.exec(statement).first()
            return user

    async def delete_user_by_email(self, email: str) -> bool:
        """通过邮箱删除用户。

        Args:
            email: 要删除的用户邮箱

        Returns:
            bool: 如果删除成功则返回 True，如果未找到用户则返回 False
        """
        with Session(self.engine) as session:
            user = session.exec(select(BaseUser).where(BaseUser.email == email)).first()
            if not user:
                return False

            session.delete(user)
            session.commit()
            logger.info("user_deleted", email=email)
            return True

    async def create_bearer_token(
        self, user_id: int, name: Optional[str] = None, expires_in_days: int = 90
    ) -> tuple[ApiKey, str]:
        """为用户创建 API Key（长期 API 密钥）。

        Args:
            user_id: 用户 ID
            name: API Key 名称（可选）
            expires_in_days: API Key 有效期（天数）

        Returns:
            tuple[ApiKey, str]: (ApiKey 模型, 原始 API Key 字符串 sk-xxx)
        """
        with Session(self.engine) as session:
            # 生成随机 API Key（sk-xxx 格式）
            raw_token = f"sk-{secrets.token_urlsafe(32)}"

            # 哈希 API Key 后存储
            token_hash = ApiKey.hash_token(raw_token)

            # 计算过期时间
            expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)

            # 创建 API Key 记录
            api_key = ApiKey(
                user_id=user_id,
                name=name or f"ApiKey-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
                token_hash=token_hash,
                expires_at=expires_at,
            )

            session.add(api_key)
            session.commit()
            session.refresh(api_key)

            logger.info("api_key_created", user_id=user_id, api_key_id=api_key.id, name=api_key.name)

            return api_key, raw_token

    async def verify_bearer_token(self, token: str) -> Optional[BaseUser]:
        """验证 API Key 并返回用户。

        Args:
            token: 原始 API Key 字符串（sk-xxx 格式）

        Returns:
            Optional[BaseUser]: 如果 API Key 有效则返回用户，否则返回 None
        """
        with Session(self.engine) as session:
            # 哈希 API Key
            token_hash = ApiKey.hash_token(token)

            # 查找 API Key
            statement = select(ApiKey).where(ApiKey.token_hash == token_hash)
            api_key = session.exec(statement).first()

            if not api_key:
                logger.warning("api_key_not_found", token_prefix=token[:10])
                return None

            # 检查 API Key 是否有效
            if not api_key.is_valid():
                logger.warning(
                    "api_key_invalid",
                    api_key_id=api_key.id,
                    revoked=api_key.revoked,
                    expired=api_key.is_expired(),
                )
                return None

            # 获取用户
            user = session.get(BaseUser, api_key.user_id)
            if not user or not user.is_active:
                logger.warning("api_key_user_inactive", user_id=api_key.user_id)
                return None

            return user

    async def revoke_bearer_token(self, token_id: int, user_id: int) -> bool:
        """撤销用户的 API Key。

        Args:
            token_id: API Key ID
            user_id: 用户 ID（用于权限验证）

        Returns:
            bool: 撤销是否成功
        """
        with Session(self.engine) as session:
            api_key = session.get(ApiKey, token_id)
            if not api_key or api_key.user_id != user_id:
                return False

            api_key.revoked = True
            session.add(api_key)
            session.commit()
            logger.info("api_key_revoked", api_key_id=token_id, user_id=user_id)
            return True

    async def get_user_api_keys(self, user_id: int) -> list[ApiKey]:
        """获取用户的所有 API Key（包括已过期和已撤销的）。

        Args:
            user_id: 用户 ID

        Returns:
            list[ApiKey]: API Key 列表
        """
        with Session(self.engine) as session:
            from sqlalchemy import desc

            statement = select(ApiKey).where(ApiKey.user_id == user_id).order_by(desc(ApiKey.created_at))
            api_keys = session.exec(statement).all()
            logger.info("api_keys_retrieved", user_id=user_id, count=len(api_keys))
            return list(api_keys)

    async def health_check(self) -> bool:
        """检查数据库连接健康状况。

        Returns:
            bool: 如果数据库健康则返回 True，否则返回 False
        """
        try:
            with Session(self.engine) as session:
                session.exec(select(1)).first()
                return True
        except Exception as e:
            logger.error("auth_service_health_check_failed", error=str(e))
            return False


# 创建单例实例
auth_service = AuthService()
