from fastapi import APIRouter, Depends
from app.schemas.user import User
from app.services.health_check_service import health_check_service
from app.core.security import get_current_user
from typing import Any, Dict


router = APIRouter(prefix="/health", tags=["Health Check"])


@router.get("")
async def health_status() -> Dict[str, str]:
    """基本健康检查"""
    return {"status": "healthy", "service": "backend-services"}


@router.get("/system")
async def system_health(current_user: User = Depends(get_current_user)) -> Any:
    """系统健康状态"""
    return health_check_service.get_system_health()


@router.get("/services")
async def services_health(current_user: User = Depends(get_current_user)) -> Any:
    """服务健康状态"""
    return await health_check_service.get_service_health()


@router.get("/detailed")
async def detailed_health(current_user: User = Depends(get_current_user)) -> Any:
    """详细健康状态"""
    return await health_check_service.get_detailed_health()


@router.get("/summary")
async def health_summary(current_user: User = Depends(get_current_user)) -> Any:
    """健康状态摘要"""
    return health_check_service.get_health_summary()