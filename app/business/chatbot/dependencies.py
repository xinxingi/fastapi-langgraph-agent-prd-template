"""Chatbot 业务模块依赖注入。

此文件提供 FastAPI 依赖注入函数，用于验证和获取聊天会话。
"""

from fastapi import Depends, HTTPException

from app.business.chatbot.models import ChatSession
from app.business.chatbot.service import chatbot_service
from app.core.auth.dependencies import get_current_user
from app.core.auth.models import BaseUser
from app.core.logging import logger
from app.utils.sanitization import sanitize_string


async def get_current_chat_session(
    session_id: str,
    current_user: BaseUser = Depends(get_current_user),
) -> ChatSession:
    """获取当前用户的聊天会话。

    此依赖注入函数验证会话是否存在且属于当前用户。

    Args:
        session_id: 会话 ID
        current_user: 当前已认证用户

    Returns:
        ChatSession: 验证成功的会话对象

    Raises:
        HTTPException: 如果会话不存在或不属于当前用户
    """
    try:
        # 清理 session_id
        session_id = sanitize_string(session_id)

        # 获取会话
        session = await chatbot_service.get_session(session_id)

        if session is None:
            logger.error("chat_session_not_found", session_id=session_id, user_id=current_user.id)
            raise HTTPException(
                status_code=404,
                detail="Session not found",
            )

        # 验证会话所有权
        if session.user_id != current_user.id:
            logger.error(
                "chat_session_unauthorized",
                session_id=session_id,
                session_user_id=session.user_id,
                current_user_id=current_user.id,
            )
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this session",
            )

        return session
    except ValueError as ve:
        logger.error("session_id_validation_failed", error=str(ve), exc_info=True)
        raise HTTPException(
            status_code=422,
            detail="Invalid session ID format",
        )
