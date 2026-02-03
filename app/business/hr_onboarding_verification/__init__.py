"""HR入职文件质量核验业务模块。

此模块提供HR入职文件质量核验功能的完整实现。
所有业务代码都在此模块内部，对外仅暴露已配置好的路由器。

自动注册：
    此模块会被业务模块注册器自动发现和注册。
"""

from fastapi import APIRouter

from app.business.hr_onboarding_verification.router import router as hr_router

# 创建业务模块的主路由器
router = APIRouter()

# 在业务模块内部完成路由注册（不传 tags，由 MODULE_CONFIG 统一管理）
router.include_router(hr_router)

# 模块配置（用于自动注册）
MODULE_CONFIG = {
    "prefix": "/hr_onboarding_verification",
    "tags": ["hr_verification"],
    "enabled": True,
    "description": "HR入职文件质量核验服务",
    "version": "1.0.0",
}

# 对外暴露
__all__ = ["router", "MODULE_CONFIG"]
