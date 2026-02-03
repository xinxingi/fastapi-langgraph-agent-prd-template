"""Chatbot 业务模块数据库模型。

此文件定义了 Chatbot 业务的会话和消息模型。
表命名遵循 cb_ 前缀规范。
"""

from datetime import datetime, UTC
from typing import Optional, List, TYPE_CHECKING, Dict, Any

from sqlalchemy import Text
from sqlmodel import Field, Relationship, Column, JSON

from app.core.models.base import BaseModel

if TYPE_CHECKING:
    pass


class ChatSession(BaseModel, table=True):
    """Chatbot 会话模型。

    对应数据库表: cb_sessions

    Attributes:
        id: 会话主键（UUID）
        user_id: 所属用户 ID（外键引用 bs_users.id）
        name: 会话名称
        extra_data: 扩展元数据（JSON 格式），存储模型配置、上下文设置等
        created_at: 创建时间（继承自 BaseModel）
        updated_at: 更新时间
        last_activity_at: 最后活跃时间
        messages: 会话消息列表（关系字段）
    """

    __tablename__ = "cb_sessions"

    id: str = Field(primary_key=True, max_length=36)
    user_id: int = Field(foreign_key="bs_users.id", index=True)
    name: str = Field(default="", max_length=100)
    extra_data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_activity_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)

    # 关系
    messages: List["ChatMessage"] = Relationship(back_populates="session", cascade_delete=True)

    def update_activity(self):
        """更新最后活跃时间。"""
        self.last_activity_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)


class ChatMessage(BaseModel, table=True):
    """Chatbot 消息模型。

    对应数据库表: cb_messages

    Attributes:
        id: 消息主键
        session_id: 所属会话 ID（外键）
        role: 消息角色（user/assistant/system）
        content: 消息内容
        extra_data: 扩展元数据（JSON 格式）
        created_at: 创建时间（继承自 BaseModel）
        session: 所属会话（关系字段）
    """

    __tablename__ = "cb_messages"

    id: int = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="cb_sessions.id", index=True, max_length=36)
    role: str = Field(max_length=50)
    content: str = Field(sa_column=Column(Text))
    extra_data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    # 关系
    session: ChatSession = Relationship(back_populates="messages")
