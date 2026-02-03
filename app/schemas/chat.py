"""此文件包含应用程序的聊天schema。"""

import re
from typing import (
    List,
    Literal,
)

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


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
        messages: 对话中的消息列表。
    """

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
