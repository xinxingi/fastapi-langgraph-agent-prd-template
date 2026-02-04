"""项目管理 API 端点。

此模块提供项目创建、更新、删除以及项目分配的端点。
"""

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.auth.dependencies import get_current_user
from app.core.auth.models import BaseUser, Project, UserProject, ApiKeyProject
from app.core.auth.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    AssignProjectToUser,
    AssignProjectToApiKey,
    UserProjectResponse,
    ApiKeyProjectResponse,
)
from app.core.auth.service import auth_service
from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import logger

router = APIRouter()


@router.post("/", response_model=ProjectResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS.get("default", ["100/minute"])[0])
async def create_project(
    request: Request, project_data: ProjectCreate, current_user: BaseUser = Depends(get_current_user)
):
    """创建新项目。

    Args:
        request: 用于速率限制的 FastAPI 请求对象
        project_data: 项目创建数据
        current_user: 已认证的用户

    Returns:
        ProjectResponse: 创建的项目信息
    """
    try:
        project = await auth_service.create_project(name=project_data.name, description=project_data.description)

        logger.info("project_created_via_api", project_id=project.id, name=project.name, user_id=current_user.id)

        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            is_active=project.is_active,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
    except ValueError as ve:
        logger.warning("project_creation_validation_failed", error=str(ve), user_id=current_user.id)
        raise HTTPException(status_code=422, detail=str(ve))


@router.get("/", response_model=ProjectListResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS.get("default", ["100/minute"])[0])
async def list_projects(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    is_active: bool | None = None,
    current_user: BaseUser = Depends(get_current_user),
):
    """获取项目列表（支持分页）。

    Args:
        request: 用于速率限制的 FastAPI 请求对象
        skip: 跳过的记录数
        limit: 返回的最大记录数
        is_active: 过滤激活状态（None 表示不过滤）
        current_user: 已认证的用户

    Returns:
        ProjectListResponse: 分页的项目列表
    """
    projects, total = await auth_service.list_projects(skip=skip, limit=limit, is_active=is_active)

    return ProjectListResponse(
        items=[
            ProjectResponse(
                id=p.id,
                name=p.name,
                description=p.description,
                is_active=p.is_active,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in projects
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{project_id}/api-keys", response_model=list[ApiKeyProjectResponse])
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS.get("default", ["100/minute"])[0])
async def get_project_api_keys(
    request: Request,
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: BaseUser = Depends(get_current_user),
):
    """获取项目的所有 API Key（支持分页）。

    Args:
        request: 用于速率限制的 FastAPI 请求对象
        project_id: 项目 ID
        skip: 跳过的记录数
        limit: 返回的最大记录数
        current_user: 已认证的用户

    Returns:
        list[ApiKeyProjectResponse]: API Key-项目关联列表
    """
    try:
        api_key_projects, total = await auth_service.get_project_api_keys(
            project_id=project_id, skip=skip, limit=limit
        )

        results = []
        for akp in api_key_projects:
            project = await auth_service.get_project(akp.project_id)
            project_response = None
            if project:
                project_response = ProjectResponse(
                    id=project.id,
                    name=project.name,
                    description=project.description,
                    is_active=project.is_active,
                    created_at=project.created_at,
                    updated_at=project.updated_at,
                )

            results.append(
                ApiKeyProjectResponse(
                    id=akp.id,
                    api_key_id=akp.api_key_id,
                    project_id=akp.project_id,
                    created_at=akp.created_at,
                    project=project_response,
                )
            )

        return results
    except ValueError as ve:
        logger.warning("project_api_keys_retrieval_failed", error=str(ve), user_id=current_user.id)
        raise HTTPException(status_code=404, detail=str(ve))


@router.get("/{project_id}", response_model=ProjectResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS.get("default", ["100/minute"])[0])
async def get_project(request: Request, project_id: int, current_user: BaseUser = Depends(get_current_user)):
    """获取项目详情。

    Args:
        request: 用于速率限制的 FastAPI 请求对象
        project_id: 项目 ID
        current_user: 已认证的用户

    Returns:
        ProjectResponse: 项目信息
    """
    project = await auth_service.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        is_active=project.is_active,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.put("/{project_id}", response_model=ProjectResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS.get("default", ["100/minute"])[0])
async def update_project(
    request: Request, project_id: int, update_data: ProjectUpdate, current_user: BaseUser = Depends(get_current_user)
):
    """更新项目信息。

    Args:
        request: 用于速率限制的 FastAPI 请求对象
        project_id: 项目 ID
        update_data: 更新数据
        current_user: 已认证的用户

    Returns:
        ProjectResponse: 更新后的项目信息
    """
    try:
        project = await auth_service.update_project(
            project_id=project_id,
            name=update_data.name,
            description=update_data.description,
            is_active=update_data.is_active,
        )

        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        logger.info("project_updated_via_api", project_id=project_id, user_id=current_user.id)

        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            is_active=project.is_active,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
    except ValueError as ve:
        logger.warning(
            "project_update_validation_failed", error=str(ve), project_id=project_id, user_id=current_user.id
        )
        raise HTTPException(status_code=422, detail=str(ve))


@router.delete("/{project_id}")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS.get("default", ["100/minute"])[0])
async def delete_project(request: Request, project_id: int, current_user: BaseUser = Depends(get_current_user)):
    """删除项目。

    Args:
        request: 用于速率限制的 FastAPI 请求对象
        project_id: 项目 ID
        current_user: 已认证的用户

    Returns:
        dict: 操作结果消息
    """
    success = await auth_service.delete_project(project_id)

    if not success:
        raise HTTPException(status_code=404, detail="项目不存在")

    logger.info("project_deleted_via_api", project_id=project_id, user_id=current_user.id)

    return {"message": "项目删除成功"}


@router.post("/assign-user", response_model=UserProjectResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS.get("default", ["100/minute"])[0])
async def assign_project_to_user(
    request: Request, assign_data: AssignProjectToUser, current_user: BaseUser = Depends(get_current_user)
):
    """为用户分配项目。

    Args:
        request: 用于速率限制的 FastAPI 请求对象
        assign_data: 分配数据
        current_user: 已认证的用户

    Returns:
        UserProjectResponse: 创建的用户-项目关联
    """
    try:
        user_project = await auth_service.assign_project_to_user(
            user_id=assign_data.user_id, project_id=assign_data.project_id, role=assign_data.role
        )

        logger.info(
            "user_assigned_to_project_via_api",
            user_id=assign_data.user_id,
            project_id=assign_data.project_id,
            role=assign_data.role,
            admin_user_id=current_user.id,
        )

        # 获取项目信息
        project = await auth_service.get_project(assign_data.project_id)
        project_response = None
        if project:
            project_response = ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                is_active=project.is_active,
                created_at=project.created_at,
                updated_at=project.updated_at,
            )

        return UserProjectResponse(
            id=user_project.id,
            user_id=user_project.user_id,
            project_id=user_project.project_id,
            role=user_project.role,
            created_at=user_project.created_at,
            project=project_response,
        )
    except ValueError as ve:
        logger.warning("user_project_assignment_failed", error=str(ve), admin_user_id=current_user.id)
        raise HTTPException(status_code=422, detail=str(ve))


@router.delete("/remove-user/{user_id}/{project_id}")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS.get("default", ["100/minute"])[0])
async def remove_project_from_user(
    request: Request, user_id: int, project_id: int, current_user: BaseUser = Depends(get_current_user)
):
    """从用户移除项目。

    Args:
        request: 用于速率限制的 FastAPI 请求对象
        user_id: 用户 ID
        project_id: 项目 ID
        current_user: 已认证的用户

    Returns:
        dict: 操作结果消息
    """
    success = await auth_service.remove_project_from_user(user_id=user_id, project_id=project_id)

    if not success:
        raise HTTPException(status_code=404, detail="用户-项目关联不存在")

    logger.info(
        "user_removed_from_project_via_api", user_id=user_id, project_id=project_id, admin_user_id=current_user.id
    )

    return {"message": "用户项目移除成功"}


@router.get("/user-projects/{user_id}", response_model=list[UserProjectResponse])
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS.get("default", ["100/minute"])[0])
async def get_user_projects(
    request: Request, user_id: int, skip: int = 0, limit: int = 100, current_user: BaseUser = Depends(get_current_user)
):
    """获取用户的所有项目（支持分页）。

    Args:
        request: 用于速率限制的 FastAPI 请求对象
        user_id: 用户 ID
        skip: 跳过的记录数
        limit: 返回的最大记录数
        current_user: 已认证的用户

    Returns:
        list[UserProjectResponse]: 用户-项目关联列表
    """
    user_projects, total = await auth_service.get_user_projects(user_id=user_id, skip=skip, limit=limit)

    results = []
    for up in user_projects:
        project = await auth_service.get_project(up.project_id)
        project_response = None
        if project:
            project_response = ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                is_active=project.is_active,
                created_at=project.created_at,
                updated_at=project.updated_at,
            )

        results.append(
            UserProjectResponse(
                id=up.id,
                user_id=up.user_id,
                project_id=up.project_id,
                role=up.role,
                created_at=up.created_at,
                project=project_response,
            )
        )

    return results


@router.post("/assign-api-key", response_model=ApiKeyProjectResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS.get("default", ["100/minute"])[0])
async def assign_project_to_api_key(
    request: Request, assign_data: AssignProjectToApiKey, current_user: BaseUser = Depends(get_current_user)
):
    """为 API Key 分配项目。

    Args:
        request: 用于速率限制的 FastAPI 请求对象
        assign_data: 分配数据
        current_user: 已认证的用户

    Returns:
        ApiKeyProjectResponse: 创建的 API Key-项目关联
    """
    try:
        api_key_project = await auth_service.assign_project_to_api_key(
            api_key_id=assign_data.api_key_id, project_id=assign_data.project_id, user_id=current_user.id
        )

        logger.info(
            "api_key_assigned_to_project_via_api",
            api_key_id=assign_data.api_key_id,
            project_id=assign_data.project_id,
            user_id=current_user.id,
        )

        # 获取项目信息
        project = await auth_service.get_project(assign_data.project_id)
        project_response = None
        if project:
            project_response = ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                is_active=project.is_active,
                created_at=project.created_at,
                updated_at=project.updated_at,
            )

        return ApiKeyProjectResponse(
            id=api_key_project.id,
            api_key_id=api_key_project.api_key_id,
            project_id=api_key_project.project_id,
            created_at=api_key_project.created_at,
            project=project_response,
        )
    except ValueError as ve:
        logger.warning("api_key_project_assignment_failed", error=str(ve), user_id=current_user.id)
        raise HTTPException(status_code=422, detail=str(ve))


@router.delete("/remove-api-key/{api_key_id}/{project_id}")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS.get("default", ["100/minute"])[0])
async def remove_project_from_api_key(
    request: Request, api_key_id: int, project_id: int, current_user: BaseUser = Depends(get_current_user)
):
    """从 API Key 移除项目。

    Args:
        request: 用于速率限制的 FastAPI 请求对象
        api_key_id: API Key ID
        project_id: 项目 ID
        current_user: 已认证的用户

    Returns:
        dict: 操作结果消息
    """
    success = await auth_service.remove_project_from_api_key(
        api_key_id=api_key_id, project_id=project_id, user_id=current_user.id
    )

    if not success:
        raise HTTPException(status_code=404, detail="API Key-项目关联不存在或权限不足")

    logger.info(
        "api_key_removed_from_project_via_api",
        api_key_id=api_key_id,
        project_id=project_id,
        user_id=current_user.id,
    )

    return {"message": "API Key 项目移除成功"}


@router.get("/api-key-projects/{api_key_id}", response_model=list[ApiKeyProjectResponse])
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS.get("default", ["100/minute"])[0])
async def get_api_key_projects(
    request: Request,
    api_key_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: BaseUser = Depends(get_current_user),
):
    """获取 API Key 的所有项目（支持分页）。

    Args:
        request: 用于速率限制的 FastAPI 请求对象
        api_key_id: API Key ID
        skip: 跳过的记录数
        limit: 返回的最大记录数
        current_user: 已认证的用户

    Returns:
        list[ApiKeyProjectResponse]: API Key-项目关联列表
    """
    try:
        api_key_projects, total = await auth_service.get_api_key_projects(
            api_key_id=api_key_id, user_id=current_user.id, skip=skip, limit=limit
        )

        results = []
        for akp in api_key_projects:
            project = await auth_service.get_project(akp.project_id)
            project_response = None
            if project:
                project_response = ProjectResponse(
                    id=project.id,
                    name=project.name,
                    description=project.description,
                    is_active=project.is_active,
                    created_at=project.created_at,
                    updated_at=project.updated_at,
                )

            results.append(
                ApiKeyProjectResponse(
                    id=akp.id,
                    api_key_id=akp.api_key_id,
                    project_id=akp.project_id,
                    created_at=akp.created_at,
                    project=project_response,
                )
            )

        return results
    except ValueError as ve:
        logger.warning("api_key_projects_retrieval_failed", error=str(ve), user_id=current_user.id)
        raise HTTPException(status_code=403, detail=str(ve))
