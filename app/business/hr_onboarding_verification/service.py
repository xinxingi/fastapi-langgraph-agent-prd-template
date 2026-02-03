"""HR入职文件质量核验服务。

此模块提供与外部HR入职文件质量核验API交互的服务。
"""

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)

from app.business.hr_onboarding_verification.config import hr_config
from app.business.hr_onboarding_verification.schemas import (
    QualityInspectionRequest,
    QualityInspectionResponse,
)
from app.core.logging import logger


class HRVerificationService:
    """HR入职文件质量核验服务类。

    处理与外部质量核验API的通信。
    """

    def __init__(self):
        """初始化HR核验服务。"""
        self.base_url = hr_config.BASE_URL
        self.api_key = hr_config.API_KEY
        self.timeout = hr_config.TIMEOUT

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def verify_document(
        self,
        request_data: QualityInspectionRequest,
    ) -> QualityInspectionResponse:
        """调用质量核验API进行文件核验。

        Args:
            request_data: 质量核验请求数据

        Returns:
            QualityInspectionResponse: 核验结果

        Raises:
            httpx.HTTPError: 当API调用失败时
            Exception: 当响应解析失败时
        """
        url = f"{self.base_url}/hr_onboarding_verification/qc"
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {self.api_key}",
        }

        logger.info(
            "hr_verification_request_initiated",
            quality_inspection_type=request_data.quality_inspection_type,
            url_count=len(request_data.urls) if request_data.urls else 0,
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=request_data.model_dump(mode="json"),
                    headers=headers,
                )
                response.raise_for_status()

                result_data = response.json()
                logger.info(
                    "hr_verification_request_successful",
                    is_all_passed=result_data.get("is_all_passed"),
                    result_count=len(result_data.get("results", [])),
                )

                return QualityInspectionResponse(**result_data)

        except httpx.HTTPStatusError as e:
            logger.exception(
                "hr_verification_request_http_error",
                status_code=e.response.status_code,
                response_text=e.response.text,
            )
            raise
        except httpx.RequestError as e:
            logger.exception(
                "hr_verification_request_network_error",
                error=str(e),
            )
            raise
        except Exception as e:
            logger.exception(
                "hr_verification_request_unexpected_error",
                error=str(e),
            )
            raise
