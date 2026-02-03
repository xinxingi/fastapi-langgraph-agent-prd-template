"""HR入职文件质量核验的Schema定义。

此模块定义了HR入职文件质量核验API的请求和响应模型。
"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class QualityInspectionType(str, Enum):
    """质量核验类型枚举。

    定义支持的文件核验类型。
    """

    # 基础证件
    ID_CARD = "ID_CARD"
    BANK_CARD = "BANK_CARD"

    # 证明与报告
    MEDICAL_REPORT = "MEDICAL_REPORT"
    RESIGNATION_CERTIFICATE = "RESIGNATION_CERTIFICATE"

    # 教育与资格
    ACADEMIC_CERTIFICATE = "ACADEMIC_CERTIFICATE"
    QUALIFICATION_CERTIFICATE = "QUALIFICATION_CERTIFICATE"

    # 其他
    BACKGROUND_CHECK = "BACKGROUND_CHECK"
    JOB_APPLICATION_DECLARATION = "JOB_APPLICATION_DECLARATION"


class StripeType(str, Enum):
    """条带类型枚举。"""

    ENGINEERING = "ENGINEERING"
    ENVIRONMENT_AND_SECURITY = "ENVIRONMENT_AND_SECURITY"
    OTHER = "OTHER"


class QualityInspectionRequest(BaseModel):
    """质量核验请求模型。

    Attributes:
        base_info: 基础信息，用于与识别内容做一致性比对
        quality_inspection_type: 核验类型
        urls: 待核验文件的URL列表（仅支持PDF/PNG/JPG）
        enable_thinking: 是否启用模型思维链，默认为False
    """

    base_info: Dict[str, str] = Field(
        ...,
        description="基础信息（用于与识别内容做一致性比对）",
    )
    quality_inspection_type: QualityInspectionType = Field(
        ...,
        description="核验类型",
    )
    urls: Optional[List[str]] = Field(
        default=None,
        description="待核验文件的URL列表；只接受PDF/PNG/JPG；为空时跳过OCR直接按规则核验",
    )
    enable_thinking: bool = Field(
        default=False,
        description="是否启用模型思维链",
    )

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """验证URL格式。

        Args:
            v: 要验证的URL列表

        Returns:
            Optional[List[str]]: 验证后的URL列表

        Raises:
            ValueError: 如果URL格式不正确
        """
        if v is None:
            return v

        for url in v:
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"URL必须以http://或https://开头: {url}")

        return v


class QualityInspectionResultItem(BaseModel):
    """单个规则核验结果。

    Attributes:
        rule_item_name: 质检项名称
        extracted_content: 从文件中提取的内容，无法识别时填"无法识别"
        abnormal_info: 异常信息，仅当存在异常时返回
    """

    rule_item_name: str = Field(
        ...,
        description="质检项名称",
    )
    extracted_content: str = Field(
        ...,
        description="从文件中提取的内容，无法识别时填'无法识别'",
    )
    abnormal_info: str = Field(
        default="",
        description="异常信息，仅当存在异常时返回",
    )


class QualityInspectionResponse(BaseModel):
    """质量核验响应模型。

    Attributes:
        is_all_passed: 整体是否全部通过
        results: 规则级别的核验结果列表
    """

    is_all_passed: bool = Field(
        ...,
        description="整体是否全部通过",
    )
    results: List[QualityInspectionResultItem] = Field(
        ...,
        description="规则级别的核验结果列表",
    )
