"""Chatbot 业务模块 Schema。

此文件定义了 Chatbot 会话管理和聊天交互相关的 Pydantic 模型。
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal

from pydantic import BaseModel, Field, field_validator


# ==================== 聊天交互相关 Schema ====================


class Message(BaseModel):
    """聊天端点的消息模型。

    Attributes:
        role: 消息发送者的角色（user或assistant）。
        content: 消息的内容。
    """

    model_config = {"extra": "ignore"}

    role: Literal["user", "assistant", "system"] = Field(..., description="消息发送者的角色")
    content: str = Field(..., description="消息的内容", min_length=1, max_length=3000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """验证消息内容。

        Args:
            v: 要验证的内容

        Returns:
            str: 验证后的内容

        Raises:
            ValueError: 如果内容包含不允许的模式
        """
        # 检查可能有害的内容
        if re.search(r"<script.*?>.*?</script>", v, re.IGNORECASE | re.DOTALL):
            raise ValueError("内容包含可能有害的script标签")

        # 检查空字节
        if "\0" in v:
            raise ValueError("内容包含空字节")

        return v


class ChatRequest(BaseModel):
    """聊天端点的请求模型。

    Attributes:
        session_id: 会话 ID（必填）
        messages: 对话中的消息列表。
    """

    session_id: str = Field(..., description="会话 ID", min_length=1, max_length=36)
    messages: List[Message] = Field(
        ...,
        description="对话中的消息列表",
        min_length=1,
    )


class ChatResponse(BaseModel):
    """聊天端点的响应模型。

    Attributes:
        messages: 对话中的消息列表。
    """

    messages: List[Message] = Field(..., description="对话中的消息列表")


class StreamResponse(BaseModel):
    """流式聊天端点的响应模型。

    Attributes:
        content: 当前数据块的内容。
        done: 流是否完成。
    """

    content: str = Field(default="", description="当前数据块的内容")
    done: bool = Field(default=False, description="流是否完成")


# ==================== 会话管理相关 Schema ====================


class ChatSessionCreate(BaseModel):
    """创建聊天会话的请求模型。

    Attributes:
        name: 会话名称（可选）
        extra_data: 会话扩展数据（可选）
    """

    name: Optional[str] = Field(default="", description="会话名称", max_length=100)
    extra_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="会话扩展数据")

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: Optional[str]) -> str:
        """清理会话名称。

        Args:
            v: 要清理的名称

        Returns:
            str: 清理后的名称
        """
        if not v:
            return ""
        # 移除任何可能有害的字符
        sanitized = re.sub(r'[<>{}[\]()\'"`]', "", v)
        return sanitized


class ChatSessionUpdate(BaseModel):
    """更新聊天会话的请求模型。

    Attributes:
        name: 会话名称（可选）
        extra_data: 会话扩展数据（可选）
    """

    name: Optional[str] = Field(default=None, description="会话名称", max_length=100)
    extra_data: Optional[Dict[str, Any]] = Field(default=None, description="会话扩展数据")

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: Optional[str]) -> Optional[str]:
        """清理会话名称。

        Args:
            v: 要清理的名称

        Returns:
            Optional[str]: 清理后的名称
        """
        if v is None:
            return None
        if not v:
            return ""
        # 移除任何可能有害的字符
        sanitized = re.sub(r'[<>{}[\]()\'"`]', "", v)
        return sanitized


class ChatSessionResponse(BaseModel):
    """聊天会话的响应模型。

    Attributes:
        id: 会话 ID
        user_id: 所属用户 ID
        name: 会话名称
        extra_data: 会话扩展数据
        created_at: 创建时间
        updated_at: 更新时间
        last_activity_at: 最后活跃时间
    """

    id: str = Field(..., description="会话 ID")
    user_id: int = Field(..., description="所属用户 ID")
    name: str = Field(..., description="会话名称")
    extra_data: Dict[str, Any] = Field(default_factory=dict, description="会话扩展数据")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_activity_at: datetime = Field(..., description="最后活跃时间")


class ChatMessageCreate(BaseModel):
    """创建聊天消息的请求模型。

    Attributes:
        role: 消息角色
        content: 消息内容
        extra_data: 消息扩展数据（可选）
    """

    role: str = Field(..., description="消息角色（user/assistant/system）", max_length=50)
    content: str = Field(..., description="消息内容")
    extra_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="消息扩展数据")


class ChatMessageResponse(BaseModel):
    """聊天消息的响应模型。

    Attributes:
        id: 消息 ID
        session_id: 所属会话 ID
        role: 消息角色
        content: 消息内容
        extra_data: 消息扩展数据
        created_at: 创建时间
    """

    id: int = Field(..., description="消息 ID")
    session_id: str = Field(..., description="所属会话 ID")
    role: str = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    extra_data: Dict[str, Any] = Field(default_factory=dict, description="消息扩展数据")
    created_at: datetime = Field(..., description="创建时间")
