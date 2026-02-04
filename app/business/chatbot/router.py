"""Chatbot 业务模块 - 路由定义（重构版本）。

此模块提供：
1. 会话管理端点（创建、列表、更新、删除）
2. 聊天交互端点（常规聊天、流式聊天）
3. 消息历史管理
"""

import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.business.chatbot.dependencies import get_current_chat_session
from app.business.chatbot.models import ChatSession
from app.business.chatbot.schemas import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionUpdate,
    ChatRequest,
    ChatResponse,
    StreamResponse,
)
from app.business.chatbot.service import chatbot_service
from app.core.auth.dependencies import get_current_user
from app.core.auth.models import BaseUser
from app.core.config import settings
from app.core.langgraph.graph import LangGraphAgent
from app.core.limiter import limiter
from app.core.logging import logger
from app.core.metrics import llm_stream_duration_seconds
from app.utils.sanitization import sanitize_string

router = APIRouter()
agent = LangGraphAgent()


# ==================== 会话管理端点 ====================


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(session_data: ChatSessionCreate, current_user: BaseUser = Depends(get_current_user)):
    """为已认证用户创建新的聊天会话。

    Args:
        session_data: 会话创建数据
        current_user: 已认证的用户

    Returns:
        ChatSessionResponse: 会话信息
    """
    try:
        session = await chatbot_service.create_session(
            user_id=current_user.id, name=session_data.name or "", extra_data=session_data.extra_data
        )

        logger.info("chat_session_created", session_id=session.id, user_id=current_user.id, name=session.name)

        return ChatSessionResponse(
            id=session.id,
            user_id=session.user_id,
            name=session.name,
            extra_data=session.extra_data,
            created_at=session.created_at,
            updated_at=session.updated_at,
            last_activity_at=session.last_activity_at,
        )
    except ValueError as ve:
        logger.warning("session_creation_validation_failed", error=str(ve), user_id=current_user.id)
        raise HTTPException(status_code=422, detail=str(ve))


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_user_sessions(current_user: BaseUser = Depends(get_current_user)):
    """获取已认证用户的所有聊天会话。

    Args:
        current_user: 已认证的用户

    Returns:
        List[ChatSessionResponse]: 会话列表
    """
    try:
        sessions = await chatbot_service.get_user_sessions(current_user.id)
        return [
            ChatSessionResponse(
                id=session.id,
                user_id=session.user_id,
                name=session.name,
                extra_data=session.extra_data,
                created_at=session.created_at,
                updated_at=session.updated_at,
                last_activity_at=session.last_activity_at,
            )
            for session in sessions
        ]
    except ValueError as ve:
        logger.warning("get_sessions_validation_failed", user_id=current_user.id, error=str(ve))
        raise HTTPException(status_code=422, detail=str(ve))


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(session_id: str, session: ChatSession = Depends(get_current_chat_session)):
    """获取会话详情。

    Args:
        session_id: 会话 ID
        session: 当前会话（依赖注入已验证所有权）

    Returns:
        ChatSessionResponse: 会话详情
    """
    return ChatSessionResponse(
        id=session.id,
        user_id=session.user_id,
        name=session.name,
        extra_data=session.extra_data,
        created_at=session.created_at,
        updated_at=session.updated_at,
        last_activity_at=session.last_activity_at,
    )


@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(
    session_id: str,
    session_data: ChatSessionUpdate,
    session: ChatSession = Depends(get_current_chat_session),
):
    """更新会话信息。

    Args:
        session_id: 会话 ID
        session_data: 会话更新数据
        session: 当前会话（依赖注入已验证所有权）

    Returns:
        ChatSessionResponse: 更新后的会话信息
    """
    try:
        updated_session = await chatbot_service.update_session(
            session_id=session_id, name=session_data.name, extra_data=session_data.extra_data
        )

        logger.info("chat_session_updated", session_id=session_id, user_id=session.user_id)

        return ChatSessionResponse(
            id=updated_session.id,
            user_id=updated_session.user_id,
            name=updated_session.name,
            extra_data=updated_session.extra_data,
            created_at=updated_session.created_at,
            updated_at=updated_session.updated_at,
            last_activity_at=updated_session.last_activity_at,
        )
    except ValueError as ve:
        logger.warning("session_update_validation_failed", error=str(ve), session_id=session_id)
        raise HTTPException(status_code=422, detail=str(ve))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, session: ChatSession = Depends(get_current_chat_session)):
    """删除会话。

    Args:
        session_id: 会话 ID
        session: 当前会话（依赖注入已验证所有权）

    Returns:
        dict: 操作结果消息
    """
    try:
        # 清理输入
        sanitized_session_id = sanitize_string(session_id)

        # 删除会话
        await chatbot_service.delete_session(sanitized_session_id)

        logger.info("chat_session_deleted", session_id=session_id, user_id=session.user_id)

        return {"message": "Session deleted successfully"}
    except ValueError as ve:
        logger.warning("session_deletion_validation_failed", error=str(ve), session_id=session_id)
        raise HTTPException(status_code=422, detail=str(ve))


# ==================== 聊天交互端点 ====================


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["chat"][0])
async def chat(
    request: Request,
    chat_request: ChatRequest,
    current_user: BaseUser = Depends(get_current_user),
):
    """使用 LangGraph 处理聊天请求。

    Args:
        request: 用于速率限制的 FastAPI 请求对象。
        chat_request: 包含消息和 session_id 的聊天请求。
        current_user: 已认证的用户

    Returns:
        ChatResponse: 处理后的聊天响应。

    Raises:
        HTTPException: 如果处理请求时出错。
    """
    try:
        # 验证会话所有权
        session = await get_current_chat_session(chat_request.session_id, current_user)

        logger.info(
            "chat_request_received",
            session_id=session.id,
            message_count=len(chat_request.messages),
        )

        # 调用 LangGraph Agent 处理聊天
        result = await agent.get_response(chat_request.messages, session.id, user_id=str(session.user_id))

        # 更新会话活跃时间
        await chatbot_service.update_session_activity(session.id)

        logger.info("chat_request_processed", session_id=session.id)

        return ChatResponse(messages=result)
    except Exception as e:
        logger.exception("chat_request_failed", session_id=chat_request.session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["chat_stream"][0])
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    current_user: BaseUser = Depends(get_current_user),
):
    """使用 LangGraph 处理聊天请求并流式返回响应。

    Args:
        request: 用于速率限制的 FastAPI 请求对象。
        chat_request: 包含消息和 session_id 的聊天请求。
        current_user: 已认证的用户

    Returns:
        StreamingResponse: 聊天完成的流式响应。

    Raises:
        HTTPException: 如果处理请求时出错。
    """
    try:
        # 验证会话所有权
        session = await get_current_chat_session(chat_request.session_id, current_user)

        logger.info(
            "stream_chat_request_received",
            session_id=session.id,
            message_count=len(chat_request.messages),
        )

        async def event_generator():
            """生成流式事件。

            Yields:
                str: JSON 格式的服务器发送事件。

            Raises:
                Exception: 如果流式传输过程中出错。
            """
            try:
                full_response = ""
                with llm_stream_duration_seconds.labels(model=agent.llm_service.get_llm().get_name()).time():
                    async for chunk in agent.get_stream_response(
                        chat_request.messages, session.id, user_id=str(session.user_id)
                    ):
                        full_response += chunk
                        response = StreamResponse(content=chunk, done=False)
                        yield f"data: {json.dumps(response.model_dump())}\n\n"

                # 更新会话活跃时间
                await chatbot_service.update_session_activity(session.id)

                # 发送表示完成的最终消息
                final_response = StreamResponse(content="", done=True)
                yield f"data: {json.dumps(final_response.model_dump())}\n\n"

            except Exception as e:
                logger.exception(
                    "stream_chat_request_failed",
                    session_id=session.id,
                    error=str(e),
                )
                error_response = StreamResponse(content=str(e), done=True)
                yield f"data: {json.dumps(error_response.model_dump())}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        logger.exception(
            "stream_chat_request_failed",
            session_id=chat_request.session_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 消息历史管理端点 ====================


@router.get("/messages", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def get_session_messages(
    request: Request,
    session: ChatSession = Depends(get_current_chat_session),
):
    """获取会话的所有消息。

    Args:
        request: 用于速率限制的 FastAPI 请求对象。
        session: 当前会话（依赖注入已验证所有权）

    Returns:
        ChatResponse: 会话中的所有消息。

    Raises:
        HTTPException: 如果检索消息时出错。
    """
    try:
        messages = await agent.get_chat_history(session.id)
        return ChatResponse(messages=messages)
    except Exception as e:
        logger.exception("get_messages_failed", session_id=session.id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/messages")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def clear_chat_history(
    request: Request,
    session: ChatSession = Depends(get_current_chat_session),
):
    """清除会话的所有消息。

    Args:
        request: 用于速率限制的 FastAPI 请求对象。
        session: 当前会话（依赖注入已验证所有权）

    Returns:
        dict: 表示聊天历史已清除的消息。
    """
    try:
        await agent.clear_chat_history(session.id)
        return {"message": "Chat history cleared successfully"}
    except Exception as e:
        logger.exception("clear_chat_history_failed", session_id=session.id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
