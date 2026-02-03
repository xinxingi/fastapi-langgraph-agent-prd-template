"""API v1 路由器配置。

此模块设置主 API 路由器，并包含用于不同端点的所有子路由器，
例如身份验证和聊天机器人功能。
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.chatbot import router as chatbot_router
from app.core.logging import logger

api_router = APIRouter()

# 包含子路由器
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(chatbot_router, prefix="/chatbot", tags=["chatbot"])


@api_router.get("/health")
async def health_check():
    """健康检查端点。

    Returns:
        dict: 健康状态信息。
    """
    logger.info("health_check_called")
    return {"status": "healthy", "version": "1.0.0"}
