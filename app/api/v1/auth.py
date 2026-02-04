"""框架层认证 API 端点。

此模块提供用户注册、登录和 Token 管理的端点。
"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request

from app.core.auth.dependencies import get_current_user
from app.core.auth.jwt import create_access_token
from app.core.auth.models import BaseUser
from app.core.auth.schemas import (
    ApiKeyCreate,
    ApiKeyListItem,
    ApiKeyResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.core.auth.service import auth_service
from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import bind_context, logger
from app.utils.sanitization import sanitize_email, sanitize_string, validate_password_strength

router = APIRouter()


@router.post("/register", response_model=UserResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["register"][0])
async def register_user(request: Request, user_data: UserCreate):
    """注册新用户。

    Args:
        request: 用于速率限制的 FastAPI 请求对象。
        user_data: 用户注册数据

    Returns:
        UserResponse: 创建的用户信息
    """
    try:
        # 清理电子邮件
        sanitized_email = sanitize_email(user_data.email)

        # 提取并验证密码
        password = user_data.password.get_secret_value()
        validate_password_strength(password)

        # 检查用户是否存在
        if await auth_service.get_user_by_email(sanitized_email):
            raise HTTPException(status_code=400, detail="Email already registered")

        # 创建用户
        user = await auth_service.create_user(email=sanitized_email, password=BaseUser.hash_password(password))

        logger.info("user_registered", user_id=user.id, email=sanitized_email)

        return UserResponse(id=user.id, email=user.email)
    except ValueError as ve:
        logger.error("user_registration_validation_failed", error=str(ve), exc_info=True)
        raise HTTPException(status_code=422, detail=str(ve))


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["login"][0])
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    grant_type: str = Form(default="password"),
):
    """用户登录。

    Args:
        request: 用于速率限制的 FastAPI 请求对象。
        username: 用户的电子邮件
        password: 用户的密码
        grant_type: 必须是 "password"

    Returns:
        TokenResponse: JWT Token 信息

    Raises:
        HTTPException: 如果凭据无效
    """
    try:
        # 清理输入（密码不应该被清理，会影响特殊字符）
        username = sanitize_email(username)  # 使用 sanitize_email 统一转小写
        # password 不清理，直接用于验证
        grant_type = sanitize_string(grant_type)

        # 验证授权类型
        if grant_type != "password":
            raise HTTPException(
                status_code=400,
                detail="Unsupported grant type. Must be 'password'",
            )

        user = await auth_service.get_user_by_email(username)
        if not user or not user.verify_password(password):
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=401,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 创建 JWT Token
        from datetime import timedelta, datetime, UTC

        access_token = create_access_token(user.id)
        expires_at = datetime.now(UTC) + timedelta(days=settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS)

        logger.info("user_logged_in", user_id=user.id, email=user.email)

        return TokenResponse(access_token=access_token, expires_at=expires_at)
    except ValueError as ve:
        logger.error("login_validation_failed", error=str(ve), exc_info=True)
        raise HTTPException(status_code=422, detail=str(ve))


@router.post("/tokens", response_model=ApiKeyResponse)
async def create_api_key(token_data: ApiKeyCreate, current_user: BaseUser = Depends(get_current_user)):
    """为已认证用户创建新的 API Key（长期 API 密钥）。

    注意：返回的 API Key 使用 Bearer 认证方案传递（Authorization: Bearer sk-xxx）

    Args:
        token_data: API Key 创建参数
        current_user: 已认证的用户

    Returns:
        ApiKeyResponse: 创建的 API Key 信息（包含原始 API Key 字符串 sk-xxx）
    """
    try:
        api_key, raw_token = await auth_service.create_bearer_token(
            current_user.id, name=token_data.name, expires_in_days=token_data.expires_in_days
        )

        logger.info(
            "api_key_created",
            user_id=current_user.id,
            api_key_id=api_key.id,
            name=api_key.name,
        )

        return ApiKeyResponse(
            id=api_key.id,
            name=api_key.name or "",
            token=raw_token,
            expires_at=api_key.expires_at,
            created_at=api_key.created_at,
        )
    except ValueError as ve:
        logger.error("api_key_creation_validation_failed", error=str(ve), user_id=current_user.id, exc_info=True)
        raise HTTPException(status_code=422, detail=str(ve))


@router.delete("/tokens/{token_id}")
async def revoke_api_key(token_id: int, current_user: BaseUser = Depends(get_current_user)):
    """撤销已认证用户的 API Key。

    Args:
        token_id: 要撤销的 API Key ID
        current_user: 已认证的用户

    Returns:
        dict: 操作结果消息
    """
    try:
        success = await auth_service.revoke_bearer_token(token_id, current_user.id)

        if not success:
            raise HTTPException(status_code=404, detail="API Key not found or does not belong to you")

        logger.info("api_key_revoked", api_key_id=token_id, user_id=current_user.id)

        return {"message": "API Key revoked successfully"}
    except ValueError as ve:
        logger.error(
            "api_key_revocation_validation_failed",
            error=str(ve),
            api_key_id=token_id,
            user_id=current_user.id,
            exc_info=True,
        )
        raise HTTPException(status_code=422, detail=str(ve))


@router.get("/tokens", response_model=list[ApiKeyListItem])
async def list_api_keys(current_user: BaseUser = Depends(get_current_user)):
    """获取已认证用户的所有 API Key 列表。

    Args:
        current_user: 已认证的用户

    Returns:
        list[ApiKeyListItem]: API Key 列表（不包含 token 字段）
    """
    api_keys = await auth_service.get_user_api_keys(current_user.id)

    return [
        ApiKeyListItem(
            id=key.id,
            name=key.name or "",
            expires_at=key.expires_at,
            created_at=key.created_at,
            revoked=key.revoked,
        )
        for key in api_keys
    ]
