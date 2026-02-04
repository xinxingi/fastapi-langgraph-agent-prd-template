"""框架层认证服务。

此文件提供用户注册、登录、Token 管理等服务。
"""

import secrets
from datetime import datetime, timedelta, UTC
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool
from sqlmodel import Session, create_engine, select

from app.core.auth.models import BaseUser, ApiKey, Project, UserProject, ApiKeyProject
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
            name: API Key 名称（可选，同一用户下必须唯一）
            expires_in_days: API Key 有效期（天数）

        Returns:
            tuple[ApiKey, str]: (ApiKey 模型, 原始 API Key 字符串 sk-xxx)

        Raises:
            ValueError: 如果名称已存在
        """
        with Session(self.engine) as session:
            # 如果提供了名称，检查是否已存在
            if name:
                existing = session.exec(select(ApiKey).where(ApiKey.user_id == user_id, ApiKey.name == name)).first()
                if existing:
                    raise ValueError(f"API Key 名称 '{name}' 已存在，请使用其他名称")

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

            # 更新最后使用时间（仅当字段存在时）
            try:
                api_key.last_used_at = datetime.now(UTC)
                session.add(api_key)
                session.commit()
            except Exception as e:
                # 如果字段不存在，忽略错误并继续
                logger.debug("last_used_at_update_skipped", error=str(e))
                session.rollback()

            return user

    async def revoke_bearer_token(self, token_id: int, user_id: int) -> bool:
        """撤销用户的 API Key。

        Args:
            token_id: API Key ID
            user_id: 用户 ID（用于权限验证）

        Returns:
            bool: 撤销是否成功

        Raises:
            ValueError: 如果 API Key 已绑定项目，无法撤销
        """
        with Session(self.engine) as session:
            api_key = session.get(ApiKey, token_id)
            if not api_key or api_key.user_id != user_id:
                return False

            # 检查是否有项目绑定了这个 API Key
            bound_projects = session.exec(select(ApiKeyProject).where(ApiKeyProject.api_key_id == token_id)).all()

            if bound_projects:
                # 获取绑定的项目名称
                project_ids = [bp.project_id for bp in bound_projects]
                projects = session.exec(select(Project).where(Project.id.in_(project_ids))).all()
                project_names = [p.name for p in projects]
                raise ValueError(
                    f"无法撤销此 API Key，因为它已被以下项目使用：{', '.join(project_names)}。"
                    f"请先从这些项目中移除该 API Key，然后再撤销。"
                )

            api_key.revoked = True
            session.add(api_key)
            session.commit()
            logger.info("api_key_revoked", api_key_id=token_id, user_id=user_id)
            return True

    async def get_user_api_keys(self, user_id: int, skip: int = 0, limit: int = 100) -> tuple[list[ApiKey], int]:
        """获取用户的所有 API Key（包括已过期和已撤销的），支持分页。

        Args:
            user_id: 用户 ID
            skip: 跳过的记录数（用于分页）
            limit: 返回的最大记录数

        Returns:
            tuple[list[ApiKey], int]: (API Key 列表, 总记录数)
        """
        with Session(self.engine) as session:
            from sqlalchemy import desc, func

            # 获取总数
            count_statement = select(func.count(ApiKey.id)).where(ApiKey.user_id == user_id)
            total = session.exec(count_statement).one()

            # 获取分页数据
            statement = (
                select(ApiKey)
                .where(ApiKey.user_id == user_id)
                .order_by(desc(ApiKey.created_at))
                .offset(skip)
                .limit(limit)
            )
            api_keys = session.exec(statement).all()
            logger.info(
                "api_keys_retrieved", user_id=user_id, count=len(api_keys), total=total, skip=skip, limit=limit
            )
            return list(api_keys), total

    async def update_api_key_expiry(self, token_id: int, user_id: int, expires_in_days: int) -> Optional[ApiKey]:
        """更新 API Key 的过期时间。

        Args:
            token_id: API Key ID
            user_id: 用户 ID（用于权限验证）
            expires_in_days: 新的有效期（天数）

        Returns:
            Optional[ApiKey]: 更新后的 API Key，如果不存在或权限不足则返回 None
        """
        with Session(self.engine) as session:
            api_key = session.get(ApiKey, token_id)
            if not api_key or api_key.user_id != user_id:
                return None

            # 计算新的过期时间
            from datetime import datetime, timedelta, UTC

            max_date = datetime(2099, 12, 31, tzinfo=UTC)
            new_expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)

            if new_expires_at > max_date:
                raise ValueError("过期时间不能超过 2099 年 12 月 31 日")

            api_key.expires_at = new_expires_at
            session.add(api_key)
            session.commit()
            session.refresh(api_key)

            logger.info(
                "api_key_updated",
                api_key_id=token_id,
                user_id=user_id,
                new_expires_at=new_expires_at.isoformat(),
            )
            return api_key

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

    # ==================== 项目管理方法 ====================

    async def create_project(self, name: str, description: Optional[str] = None) -> Project:
        """创建新项目。

        Args:
            name: 项目名称（唯一）
            description: 项目描述

        Returns:
            Project: 创建的项目

        Raises:
            ValueError: 如果项目名称已存在
        """
        with Session(self.engine) as session:
            # 检查项目名是否已存在
            existing = session.exec(select(Project).where(Project.name == name)).first()
            if existing:
                raise ValueError(f"项目名称 '{name}' 已存在")

            project = Project(name=name, description=description)
            session.add(project)
            session.commit()
            session.refresh(project)
            logger.info("project_created", project_id=project.id, name=name)
            return project

    async def get_project(self, project_id: int) -> Optional[Project]:
        """通过 ID 获取项目。

        Args:
            project_id: 项目 ID

        Returns:
            Optional[Project]: 如果找到则返回项目，否则返回 None
        """
        with Session(self.engine) as session:
            project = session.get(Project, project_id)
            return project

    async def get_project_by_name(self, name: str) -> Optional[Project]:
        """通过名称获取项目。

        Args:
            name: 项目名称

        Returns:
            Optional[Project]: 如果找到则返回项目，否则返回 None
        """
        with Session(self.engine) as session:
            statement = select(Project).where(Project.name == name)
            project = session.exec(statement).first()
            return project

    async def update_project(
        self,
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[Project]:
        """更新项目信息。

        Args:
            project_id: 项目 ID
            name: 新的项目名称
            description: 新的项目描述
            is_active: 项目是否激活

        Returns:
            Optional[Project]: 更新后的项目，如果不存在则返回 None

        Raises:
            ValueError: 如果新名称已被其他项目使用
        """
        with Session(self.engine) as session:
            project = session.get(Project, project_id)
            if not project:
                return None

            # 如果要更新名称，检查是否重复
            if name and name != project.name:
                existing = session.exec(select(Project).where(Project.name == name)).first()
                if existing:
                    raise ValueError(f"项目名称 '{name}' 已被使用")
                project.name = name

            if description is not None:
                project.description = description

            if is_active is not None:
                project.is_active = is_active

            project.updated_at = datetime.now(UTC)
            session.add(project)
            session.commit()
            session.refresh(project)

            logger.info("project_updated", project_id=project_id)
            return project

    async def delete_project(self, project_id: int) -> bool:
        """删除项目。

        Args:
            project_id: 项目 ID

        Returns:
            bool: 如果删除成功则返回 True，如果未找到项目则返回 False
        """
        with Session(self.engine) as session:
            project = session.get(Project, project_id)
            if not project:
                return False

            session.delete(project)
            session.commit()
            logger.info("project_deleted", project_id=project_id)
            return True

    async def list_projects(
        self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
    ) -> tuple[list[Project], int]:
        """获取项目列表（支持分页）。

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            is_active: 过滤激活状态（None 表示不过滤）

        Returns:
            tuple[list[Project], int]: (项目列表, 总记录数)
        """
        with Session(self.engine) as session:
            from sqlalchemy import desc, func

            # 构建查询条件
            statement = select(Project)
            count_statement = select(func.count(Project.id))

            if is_active is not None:
                statement = statement.where(Project.is_active == is_active)
                count_statement = count_statement.where(Project.is_active == is_active)

            # 获取总数
            total = session.exec(count_statement).one()

            # 获取分页数据
            statement = statement.order_by(desc(Project.created_at)).offset(skip).limit(limit)
            projects = session.exec(statement).all()

            logger.info("projects_retrieved", count=len(projects), total=total, skip=skip, limit=limit)
            return list(projects), total

    async def assign_project_to_user(self, user_id: int, project_id: int, role: str = "member") -> UserProject:
        """为用户分配项目。

        Args:
            user_id: 用户 ID
            project_id: 项目 ID
            role: 用户在项目中的角色

        Returns:
            UserProject: 创建的用户-项目关联

        Raises:
            ValueError: 如果用户或项目不存在，或关联已存在
        """
        with Session(self.engine) as session:
            # 检查用户和项目是否存在
            user = session.get(BaseUser, user_id)
            if not user:
                raise ValueError(f"用户 ID {user_id} 不存在")

            project = session.get(Project, project_id)
            if not project:
                raise ValueError(f"项目 ID {project_id} 不存在")

            # 检查关联是否已存在
            existing = session.exec(
                select(UserProject).where(UserProject.user_id == user_id, UserProject.project_id == project_id)
            ).first()
            if existing:
                raise ValueError(f"用户 {user_id} 已被分配到项目 {project_id}")

            user_project = UserProject(user_id=user_id, project_id=project_id, role=role)
            session.add(user_project)
            session.commit()
            session.refresh(user_project)

            logger.info("user_assigned_to_project", user_id=user_id, project_id=project_id, role=role)
            return user_project

    async def remove_project_from_user(self, user_id: int, project_id: int) -> bool:
        """从用户移除项目。

        Args:
            user_id: 用户 ID
            project_id: 项目 ID

        Returns:
            bool: 如果移除成功则返回 True，如果关联不存在则返回 False
        """
        with Session(self.engine) as session:
            user_project = session.exec(
                select(UserProject).where(UserProject.user_id == user_id, UserProject.project_id == project_id)
            ).first()

            if not user_project:
                return False

            session.delete(user_project)
            session.commit()
            logger.info("user_removed_from_project", user_id=user_id, project_id=project_id)
            return True

    async def get_user_projects(self, user_id: int, skip: int = 0, limit: int = 100) -> tuple[list[UserProject], int]:
        """获取用户的所有项目（支持分页）。

        Args:
            user_id: 用户 ID
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            tuple[list[UserProject], int]: (用户-项目关联列表, 总记录数)
        """
        with Session(self.engine) as session:
            from sqlalchemy import desc, func

            # 获取总数
            count_statement = select(func.count(UserProject.id)).where(UserProject.user_id == user_id)
            total = session.exec(count_statement).one()

            # 获取分页数据
            statement = (
                select(UserProject)
                .where(UserProject.user_id == user_id)
                .order_by(desc(UserProject.created_at))
                .offset(skip)
                .limit(limit)
            )
            user_projects = session.exec(statement).all()

            logger.info("user_projects_retrieved", user_id=user_id, count=len(user_projects), total=total)
            return list(user_projects), total

    async def assign_project_to_api_key(self, api_key_id: int, project_id: int, user_id: int) -> ApiKeyProject:
        """为 API Key 分配项目。

        Args:
            api_key_id: API Key ID
            project_id: 项目 ID
            user_id: 用户 ID（用于权限验证）

        Returns:
            ApiKeyProject: 创建的 API Key-项目关联

        Raises:
            ValueError: 如果 API Key 或项目不存在，或权限不足，或关联已存在
        """
        with Session(self.engine) as session:
            # 检查 API Key 是否存在且属于该用户
            api_key = session.get(ApiKey, api_key_id)
            if not api_key or api_key.user_id != user_id:
                raise ValueError(f"API Key ID {api_key_id} 不存在或不属于您")

            # 检查项目是否存在
            project = session.get(Project, project_id)
            if not project:
                raise ValueError(f"项目 ID {project_id} 不存在")

            # 检查关联是否已存在
            existing = session.exec(
                select(ApiKeyProject).where(
                    ApiKeyProject.api_key_id == api_key_id, ApiKeyProject.project_id == project_id
                )
            ).first()
            if existing:
                raise ValueError(f"API Key {api_key_id} 已被分配到项目 {project_id}")

            api_key_project = ApiKeyProject(api_key_id=api_key_id, project_id=project_id)
            session.add(api_key_project)
            session.commit()
            session.refresh(api_key_project)

            logger.info("api_key_assigned_to_project", api_key_id=api_key_id, project_id=project_id, user_id=user_id)
            return api_key_project

    async def remove_project_from_api_key(self, api_key_id: int, project_id: int, user_id: int) -> bool:
        """从 API Key 移除项目。

        Args:
            api_key_id: API Key ID
            project_id: 项目 ID
            user_id: 用户 ID（用于权限验证）

        Returns:
            bool: 如果移除成功则返回 True，如果关联不存在或权限不足则返回 False
        """
        with Session(self.engine) as session:
            # 检查 API Key 是否属于该用户
            api_key = session.get(ApiKey, api_key_id)
            if not api_key or api_key.user_id != user_id:
                return False

            api_key_project = session.exec(
                select(ApiKeyProject).where(
                    ApiKeyProject.api_key_id == api_key_id, ApiKeyProject.project_id == project_id
                )
            ).first()

            if not api_key_project:
                return False

            session.delete(api_key_project)
            session.commit()
            logger.info("api_key_removed_from_project", api_key_id=api_key_id, project_id=project_id, user_id=user_id)
            return True

    async def get_api_key_projects(
        self, api_key_id: int, user_id: int, skip: int = 0, limit: int = 100
    ) -> tuple[list[ApiKeyProject], int]:
        """获取 API Key 的所有项目（支持分页）。

        Args:
            api_key_id: API Key ID
            user_id: 用户 ID（用于权限验证）
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            tuple[list[ApiKeyProject], int]: (API Key-项目关联列表, 总记录数)

        Raises:
            ValueError: 如果 API Key 不属于该用户
        """
        with Session(self.engine) as session:
            # 检查 API Key 是否属于该用户
            api_key = session.get(ApiKey, api_key_id)
            if not api_key or api_key.user_id != user_id:
                raise ValueError(f"API Key ID {api_key_id} 不存在或不属于您")

            from sqlalchemy import desc, func

            # 获取总数
            count_statement = select(func.count(ApiKeyProject.id)).where(ApiKeyProject.api_key_id == api_key_id)
            total = session.exec(count_statement).one()

            # 获取分页数据
            statement = (
                select(ApiKeyProject)
                .where(ApiKeyProject.api_key_id == api_key_id)
                .order_by(desc(ApiKeyProject.created_at))
                .offset(skip)
                .limit(limit)
            )
            api_key_projects = session.exec(statement).all()

            logger.info("api_key_projects_retrieved", api_key_id=api_key_id, count=len(api_key_projects), total=total)
            return list(api_key_projects), total

    async def verify_api_key_project_access(self, token: str, project_id: int) -> bool:
        """验证 API Key 是否有权访问指定项目。

        Args:
            token: 原始 API Key 字符串（sk-xxx 格式）
            project_id: 项目 ID

        Returns:
            bool: 如果有权访问则返回 True，否则返回 False
        """
        with Session(self.engine) as session:
            # 哈希 API Key
            token_hash = ApiKey.hash_token(token)

            # 查找 API Key
            statement = select(ApiKey).where(ApiKey.token_hash == token_hash)
            api_key = session.exec(statement).first()

            if not api_key or not api_key.is_valid():
                return False

            # 检查 API Key 是否有权访问该项目
            api_key_project = session.exec(
                select(ApiKeyProject).where(
                    ApiKeyProject.api_key_id == api_key.id, ApiKeyProject.project_id == project_id
                )
            ).first()

            return api_key_project is not None

    async def get_project_api_keys(
        self, project_id: int, skip: int = 0, limit: int = 100
    ) -> tuple[list[ApiKeyProject], int]:
        """获取项目的所有 API Key（支持分页）。

        Args:
            project_id: 项目 ID
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            tuple[list[ApiKeyProject], int]: (API Key-项目关联列表, 总记录数)

        Raises:
            ValueError: 如果项目不存在
        """
        with Session(self.engine) as session:
            # 检查项目是否存在
            project = session.get(Project, project_id)
            if not project:
                raise ValueError(f"项目 ID {project_id} 不存在")

            from sqlalchemy import desc, func

            # 获取总数
            count_statement = select(func.count(ApiKeyProject.id)).where(ApiKeyProject.project_id == project_id)
            total = session.exec(count_statement).one()

            # 获取分页数据
            statement = (
                select(ApiKeyProject)
                .where(ApiKeyProject.project_id == project_id)
                .order_by(desc(ApiKeyProject.created_at))
                .offset(skip)
                .limit(limit)
            )
            api_key_projects = session.exec(statement).all()

            logger.info("project_api_keys_retrieved", project_id=project_id, count=len(api_key_projects), total=total)
            return list(api_key_projects), total

    async def get_api_key_bound_projects_count(self, api_key_id: int) -> int:
        """获取 API Key 绑定的项目数量。

        Args:
            api_key_id: API Key ID

        Returns:
            int: 绑定的项目数量
        """
        with Session(self.engine) as session:
            from sqlalchemy import func

            count = session.exec(
                select(func.count(ApiKeyProject.id)).where(ApiKeyProject.api_key_id == api_key_id)
            ).one()
            return count


# 创建单例实例
auth_service = AuthService()
