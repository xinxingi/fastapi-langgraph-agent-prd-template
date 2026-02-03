"""此文件包含应用程序的会话模型。"""

from typing import (
    TYPE_CHECKING,
    List,
)

from sqlmodel import (
    Field,
    Relationship,
)

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Session(BaseModel, table=True):
    """存储聊天会话的会话模型。

    Attributes:
        id: 主键
        user_id: 用户的外键
        name: 会话名称（默认为空字符串）
        created_at: 会话创建时间
        messages: 会话消息的关系
        user: 会话所有者的关系
    """

    id: str = Field(primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str = Field(default="")
    user: "User" = Relationship(back_populates="sessions")
