"""
聊天机器人业务模块

此模块提供基于 LangGraph 的 AI 代理聊天功能。

支持常规和流式聊天回复，以及消息历史记录管理。
"""

from fastapi import APIRouter

from app.business.chatbot.router import router as chat_router

# 为此模块创建主路由器
router = APIRouter()
router.include_router(chat_router)

# 自动注册模块配置
MODULE_CONFIG = {
    "prefix": "/chatbot",
    "tags": ["chatbot", "chat"],
    "enabled": True,
    "description": "AI聊天机器人服务 - 支持常规对话和流式响应",
    "version": "1.0.0",
}

__all__ = ["router", "MODULE_CONFIG"]
