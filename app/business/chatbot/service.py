"""Chatbot 业务模块服务层。

此文件提供 Chatbot 会话和消息的数据库操作服务。
"""

import uuid
from datetime import datetime, UTC
from typing import Optional, List

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool
from sqlmodel import Session, create_engine, select

from app.business.chatbot.models import ChatSession, ChatMessage
from app.core.config import settings
from app.core.logging import logger


class ChatbotService:
    """Chatbot 业务服务类。

    该类处理聊天会话和消息的所有数据库操作。
    """

    def __init__(self):
        """初始化 Chatbot 服务，创建数据库引擎和表。"""
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
                "chatbot_service_initialized",
                pool_size=pool_size,
                max_overflow=max_overflow,
            )
        except SQLAlchemyError as e:
            logger.error("chatbot_service_initialization_error", error=str(e))
            raise

    async def create_session(self, user_id: int, name: str = "", extra_data: Optional[dict] = None) -> ChatSession:
        """创建新的聊天会话。

        Args:
            user_id: 用户 ID
            name: 会话名称
            extra_data: 会话扩展数据

        Returns:
            ChatSession: 创建的会话
        """
        with Session(self.engine) as session:
            session_id = str(uuid.uuid4())
            chat_session = ChatSession(id=session_id, user_id=user_id, name=name, extra_data=extra_data or {})
            session.add(chat_session)
            session.commit()
            session.refresh(chat_session)
            logger.info("chat_session_created", session_id=session_id, user_id=user_id, name=name)
            return chat_session

    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """通过 ID 获取会话。

        Args:
            session_id: 会话 ID

        Returns:
            Optional[ChatSession]: 如果找到则返回会话，否则返回 None
        """
        with Session(self.engine) as session:
            chat_session = session.get(ChatSession, session_id)
            return chat_session

    async def get_user_sessions(self, user_id: int) -> List[ChatSession]:
        """获取用户的所有会话。

        Args:
            user_id: 用户 ID

        Returns:
            List[ChatSession]: 用户的会话列表
        """
        with Session(self.engine) as session:
            statement = (
                select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.last_activity_at.desc())
            )
            sessions = session.exec(statement).all()
            return list(sessions)

    async def update_session(
        self, session_id: str, name: Optional[str] = None, extra_data: Optional[dict] = None
    ) -> ChatSession:
        """更新会话。

        Args:
            session_id: 会话 ID
            name: 新的会话名称（可选）
            extra_data: 新的会话扩展数据（可选）

        Returns:
            ChatSession: 更新后的会话

        Raises:
            HTTPException: 如果未找到会话
        """
        with Session(self.engine) as session:
            chat_session = session.get(ChatSession, session_id)
            if not chat_session:
                raise HTTPException(status_code=404, detail="Session not found")

            if name is not None:
                chat_session.name = name
            if extra_data is not None:
                chat_session.extra_data = extra_data

            chat_session.updated_at = datetime.now(UTC)
            session.add(chat_session)
            session.commit()
            session.refresh(chat_session)
            logger.info("chat_session_updated", session_id=session_id)
            return chat_session

    async def delete_session(self, session_id: str) -> bool:
        """删除会话。

        Args:
            session_id: 会话 ID

        Returns:
            bool: 如果删除成功则返回 True，如果未找到会话则返回 False
        """
        with Session(self.engine) as session:
            chat_session = session.get(ChatSession, session_id)
            if not chat_session:
                return False

            session.delete(chat_session)
            session.commit()
            logger.info("chat_session_deleted", session_id=session_id)
            return True

    async def update_session_activity(self, session_id: str) -> None:
        """更新会话的最后活跃时间。

        Args:
            session_id: 会话 ID
        """
        with Session(self.engine) as session:
            chat_session = session.get(ChatSession, session_id)
            if chat_session:
                chat_session.update_activity()
                session.add(chat_session)
                session.commit()

    async def create_message(
        self, session_id: str, role: str, content: str, extra_data: Optional[dict] = None
    ) -> ChatMessage:
        """创建新的聊天消息。

        Args:
            session_id: 会话 ID
            role: 消息角色（user/assistant/system）
            content: 消息内容
            extra_data: 消息扩展数据

        Returns:
            ChatMessage: 创建的消息
        """
        with Session(self.engine) as session:
            message = ChatMessage(session_id=session_id, role=role, content=content, extra_data=extra_data or {})
            session.add(message)
            session.commit()
            session.refresh(message)
            logger.info("chat_message_created", session_id=session_id, role=role)
            return message

    async def get_session_messages(self, session_id: str) -> List[ChatMessage]:
        """获取会话的所有消息。

        Args:
            session_id: 会话 ID

        Returns:
            List[ChatMessage]: 消息列表
        """
        with Session(self.engine) as session:
            statement = (
                select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
            )
            messages = session.exec(statement).all()
            return list(messages)

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
            logger.error("chatbot_service_health_check_failed", error=str(e))
            return False


# 创建单例实例
chatbot_service = ChatbotService()
