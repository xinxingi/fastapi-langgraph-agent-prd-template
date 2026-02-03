"""所有模型的基础模型和公共导入。"""

from datetime import datetime, UTC
from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship


class BaseModel(SQLModel):
    """带有公共字段的基础模型。"""

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_column_kwargs={"comment": "记录创建时间"}
    )
