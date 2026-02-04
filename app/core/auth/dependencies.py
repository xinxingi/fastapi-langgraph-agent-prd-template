"""框架层认证依赖注入。

此文件提供 FastAPI 依赖注入函数，用于验证用户身份。
支持两种认证方式：
1. JWT Token - 用户登录后获得，用于会话管理
2. Bearer Token (API Key) - 用户主动创建，用于程序调用

同时提供项目级别的权限验证，确保 API Key 只能访问被授权的项目。
"""

from typing import Optional

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


class ProjectAccessChecker:
    """项目访问权限检查器。

    这是一个依赖类，用于验证 API Key 是否有权访问指定项目。
    仅对使用 API Key (sk-xxx) 认证的请求进行项目权限检查。
    使用 JWT Token 认证的请求不受项目权限限制。

    用法：
        @router.get("/some-endpoint")
        async def endpoint(
            project_id: int,
            current_user: BaseUser = Depends(get_current_user),
            _: None = Depends(ProjectAccessChecker(project_id_param="project_id"))
        ):
            # 此端点只有拥有项目访问权限的 API Key 才能调用
            pass
    """

    def __init__(self, project_id_param: str = "project_id"):
        """初始化项目访问检查器。

        Args:
            project_id_param: 项目 ID 参数名称（默认 "project_id"）
        """
        self.project_id_param = project_id_param

    async def __call__(
        self, credentials: HTTPAuthorizationCredentials = Depends(security), project_id: Optional[int] = None
    ) -> None:
        """检查 API Key 是否有权访问指定项目。

        Args:
            credentials: HTTP 授权凭据
            project_id: 项目 ID（从路径或查询参数获取）

        Raises:
            HTTPException: 如果没有项目访问权限
        """
        try:
            # 清理 Token
            token = sanitize_string(credentials.credentials)

            # 只对 API Key 进行项目权限检查
            # JWT Token 用户不受项目权限限制
            if not token.startswith("sk-"):
                logger.debug("jwt_token_skips_project_check")
                return

            # 如果没有提供 project_id，跳过检查
            if project_id is None:
                logger.debug("no_project_id_provided_skipping_check")
                return

            # 验证 API Key 是否有权访问该项目
            has_access = await auth_service.verify_api_key_project_access(token, project_id)

            if not has_access:
                logger.warning("api_key_project_access_denied", project_id=project_id, token_prefix=token[:10] + "...")
                raise HTTPException(
                    status_code=403,
                    detail=f"API Key 无权访问项目 {project_id}",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            logger.debug("api_key_project_access_granted", project_id=project_id)

        except ValueError as ve:
            logger.warning("project_access_check_failed", error=str(ve))
            raise HTTPException(
                status_code=422,
                detail="项目权限检查失败",
                headers={"WWW-Authenticate": "Bearer"},
            )


async def require_project_access(
    project_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)
) -> None:
    """要求当前用户有权访问指定项目（简化版依赖）。

    这是一个简化的依赖函数，用于快速检查项目访问权限。
    仅对使用 API Key (sk-xxx) 认证的请求进行项目权限检查。

    Args:
        project_id: 项目 ID
        credentials: HTTP 授权凭据

    Raises:
        HTTPException: 如果没有项目访问权限

    用法：
        @router.get("/some-endpoint/{project_id}")
        async def endpoint(
            project_id: int,
            current_user: BaseUser = Depends(get_current_user),
            _: None = Depends(require_project_access)
        ):
            # 此端点只有拥有项目访问权限的 API Key 才能调用
            pass
    """
    checker = ProjectAccessChecker()
    await checker(credentials=credentials, project_id=project_id)
