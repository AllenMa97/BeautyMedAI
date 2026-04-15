from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user import User
from app.services.llm_service import llm_service, LLMRequest, LLMResponse
from app.core.security import get_current_user
from typing import Any, Dict, List


router = APIRouter(prefix="/large_model", tags=["LLM Management"])


@router.post("/chat/completions", response_model=LLMResponse)
async def llm_chat_completions(
    request: LLMRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """LLM聊天完成接口"""
    try:
        response = await llm_service.call_llm(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calling LLM: {str(e)}"
        )


@router.get("/providers")
async def list_providers(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """列出可用的LLM提供商"""
    providers_info = {}
    for name, provider in llm_service.providers.items():
        providers_info[name] = {
            "name": provider.name,
            "enabled": provider.enabled,
            "default_model": provider.default_model
        }
    return {"providers": providers_info}


@router.get("/providers/{provider_name}/models")
async def list_provider_models(
    provider_name: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, List[str]]:
    """列出特定提供商的可用模型"""
    try:
        models = await llm_service.list_available_models(provider_name)
        return {"models": models}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/providers/{provider_name}/stats")
async def get_provider_stats(
    provider_name: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """获取提供商统计信息"""
    try:
        stats = await llm_service.get_provider_stats(provider_name)
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/providers/{provider_name}/health")
async def provider_health_check(
    provider_name: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, bool]:
    """检查提供商健康状态"""
    try:
        is_healthy = await llm_service.health_check(provider_name)
        return {"provider": provider_name, "healthy": is_healthy}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )