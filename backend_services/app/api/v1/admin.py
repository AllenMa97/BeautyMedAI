from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.user import User
from app.services.user_service import get_users
from app.services.session_service import get_sessions_by_user
from app.services.health_check_service import health_check_service
from app.services.llm_service import llm_service
from app.core.database import get_db
from app.core.security import get_current_user
from typing import Any, Dict, List
from datetime import datetime


router = APIRouter(prefix="/admin", tags=["Admin Panel"])


@router.get("")
async def admin_dashboard(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """管理员仪表板"""
    if not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return {
        "message": "Welcome to Admin Dashboard",
        "timestamp": datetime.utcnow().isoformat(),
        "user": current_user.username
    }


@router.get("/users")
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """列出所有用户（仅管理员）"""
    if not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    users = get_users(db, skip=skip, limit=limit)
    return {
        "users": users,
        "total": len(users),
        "skip": skip,
        "limit": limit
    }


@router.get("/system-stats")
async def system_statistics(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """系统统计信息"""
    if not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 获取系统健康信息
    system_health = health_check_service.get_system_health()
    
    # 获取服务统计
    service_stats = await health_check_service.get_service_health()
    
    # 获取LLM服务统计
    llm_provider_stats = {}
    for provider_name in llm_service.providers:
        try:
            stats = await llm_service.get_provider_stats(provider_name)
            llm_provider_stats[provider_name] = stats.dict()
        except:
            llm_provider_stats[provider_name] = {"error": "Unable to fetch stats"}
    
    return {
        "system_health": system_health,
        "service_stats": service_stats,
        "llm_provider_stats": llm_provider_stats,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/audit-log")
async def audit_log(current_user: User = Depends(get_current_user)) -> List[Dict[str, Any]]:
    """审计日志（示例）"""
    if not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 这里应该从数据库或日志系统中获取实际的审计日志
    # 现在返回示例数据
    return [
        {
            "timestamp": "2023-10-01T10:00:00Z",
            "user": "admin",
            "action": "login",
            "resource": "admin_panel",
            "status": "success"
        },
        {
            "timestamp": "2023-10-01T10:05:00Z",
            "user": "user1",
            "action": "create_session",
            "resource": "session_api",
            "status": "success"
        }
    ]


@router.get("/config")
async def get_system_config(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """获取系统配置"""
    if not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 返回敏感配置信息的概要（不包含密钥等）
    from config.settings import settings
    
    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "api_prefix": settings.API_V1_STR,
        "cors_origins": settings.BACKEND_CORS_ORIGINS,
        "rate_limit": settings.RATE_LIMIT_REQUESTS,
        "session_timeout_hours": settings.SESSION_TIMEOUT_HOURS
    }


@router.get("/performance")
async def performance_metrics(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """性能指标"""
    if not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 获取系统性能指标
    system_health = health_check_service.get_system_health()
    
    # 获取队列性能指标
    queue_performance = {
        "queue_size": 0,
        "active_tasks": 0,
        "completed_tasks": 0
    }
    
    if hasattr(llm_service, 'stats'):
        llm_performance = {}
        for provider_name, stats in llm_service.stats.items():
            llm_performance[provider_name] = {
                "total_requests": stats.total_requests,
                "successful_requests": stats.successful_requests,
                "failed_requests": stats.failed_requests,
                "total_tokens": stats.total_tokens
            }
    else:
        llm_performance = {}
    
    return {
        "system": system_health["system"],
        "queue": queue_performance,
        "large_model": llm_performance,
        "timestamp": datetime.utcnow().isoformat()
    }