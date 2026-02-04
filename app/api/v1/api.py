"""API v1 路由器配置。

此模块设置主 API 路由器，并包含用于不同端点的所有子路由器。

业务模块自动注册：
- 框架核心路由（auth）手动注册 - 身份验证是框架级别关注点
- 业务模块（app/business/*）自动发现和注册 - 包括 chatbot, hr_verification 等
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.projects import router as projects_router
from app.core.business_registry import auto_register_business_modules
from app.core.logging import logger

api_router = APIRouter()

# 包含框架核心路由器（手动注册）
# 只有 auth 和 projects 保留在这里，因为它们是框架级别的基础设施
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])

# 自动注册所有业务模块
# 所有业务逻辑模块（chatbot, hr_verification 等）都通过自动发现注册
auto_register_business_modules(api_router=api_router, exclude=[])


@api_router.get("/health")
async def health_check():
    """健康检查端点。

    Returns:
        dict: 健康状态信息。
    """
    logger.info("health_check_called")
    return {"status": "healthy", "version": "1.0.0"}
