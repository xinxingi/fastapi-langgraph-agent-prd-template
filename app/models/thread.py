"""此文件包含应用程序的线程模型。"""

from datetime import (
    UTC,
    datetime,
)

from sqlmodel import (
    Field,
    SQLModel,
)


class Thread(SQLModel, table=True):
    """存储对话线程的线程模型。

    Attributes:
        id: 主键
        created_at: 线程创建时间
        messages: 此线程中消息的关系
    """

    id: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
