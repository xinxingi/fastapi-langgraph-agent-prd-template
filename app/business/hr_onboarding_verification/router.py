"""HR入职文件质量核验API端点。

此模块提供HR入职文件质量核验的API端点。
"""

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)

from app.business.hr_onboarding_verification.config import hr_config
from app.business.hr_onboarding_verification.schemas import (
    QualityInspectionRequest,
    QualityInspectionResponse,
)
from app.business.hr_onboarding_verification.service import HRVerificationService
from app.core.limiter import limiter
from app.core.logging import logger

router = APIRouter()
hr_service = HRVerificationService()


@router.post("/qc", response_model=QualityInspectionResponse)
@limiter.limit(hr_config.RATE_LIMIT)
async def quality_check(
    request: Request,
    qc_request: QualityInspectionRequest,
):
    """HR入职文件质量核验端点。

    对用户上传的文件（仅支持 PDF / PNG / JPG）进行质量核验/信息一致性校验，
    并结合 base_info 基础信息输出规则级别的校验结果。

    参数:
        request: 用于速率限制的 FastAPI 请求对象
        qc_request: 质量核验请求数据

    返回:
        QualityInspectionResponse: 核验结果

    异常:
        HTTPException: 如果处理请求时出错
    """
    try:
        logger.info(
            "quality_check_request_received",
            quality_inspection_type=qc_request.quality_inspection_type,
            url_count=len(qc_request.urls) if qc_request.urls else 0,
            enable_thinking=qc_request.enable_thinking,
        )

        result = await hr_service.verify_document(qc_request)

        logger.info(
            "quality_check_request_processed",
            is_all_passed=result.is_all_passed,
            result_count=len(result.results),
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "quality_check_request_failed",
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))
