from fastapi import APIRouter
from algorithm_services.api.schemas.feature_schemas.entity_recognize_schemas import (
    EntityRecognizeRequest,
    EntityRecognizeResponse
)
from algorithm_services.core.services.feature_services.entity_recognize_service import EntityRecognizeService
from algorithm_services.utils.logger import get_logger

logger = get_logger(__name__)

# 实体识别路由
router = APIRouter(
    prefix="/api/v1/feature/entity_recognize",
    tags=["核心功能 - 实体识别器"]
)

# 初始化Service
entity_service = EntityRecognizeService()

@router.post("/recognize", response_model=EntityRecognizeResponse)
async def recognize_entity(request: EntityRecognizeRequest):
    """
    实体识别API（小白友好版）
    - 输入：用户口语化表达 + 会话上下文
    - 输出：5类结构化实体（无技术术语）
    """
    logger.info(f"实体识别请求 - session_id: {request.session_id}, user_input: {request.user_input[:50]}")
    result = await entity_service.recognize(request)
    return result
