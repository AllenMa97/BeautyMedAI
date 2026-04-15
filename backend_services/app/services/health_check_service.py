from typing import Dict, Any, List
from datetime import datetime
import psutil
import asyncio
from app.services.queue_service import queue_service
from app.services.cache_service import cache_service
from app.services.gpu_manager_service import gpu_manager_service
from config.settings import settings
import httpx
import logging


logger = logging.getLogger(__name__)


class HealthCheckService:
    def __init__(self):
        self.start_time = datetime.utcnow()

    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        
        # 磁盘使用情况
        disk_usage = psutil.disk_usage('/')
        
        # 进程信息
        process = psutil.Process()
        process_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": str(datetime.utcnow() - self.start_time),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / 1024 / 1024,
                "disk_percent": disk_usage.percent,
                "process_memory_mb": round(process_memory, 2)
            }
        }

    async def get_service_health(self) -> Dict[str, Any]:
        """获取服务健康状态"""
        health_status = {
            "overall_status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {}
        }
        
        # 检查队列服务
        try:
            queue_status = {
                "status": "operational" if hasattr(queue_service, 'running') and queue_service.running else "degraded",
                "queue_size": queue_service.get_queue_size() if hasattr(queue_service, 'get_queue_size') else 0,
                "active_tasks": queue_service.get_active_task_count() if hasattr(queue_service, 'get_active_task_count') else 0
            }
            health_status["services"]["queue"] = queue_status
        except Exception as e:
            logger.error(f"Queue service health check failed: {str(e)}")
            health_status["services"]["queue"] = {"status": "error", "error": str(e)}
            health_status["overall_status"] = "degraded"

        # 检查缓存服务
        try:
            cache_connected = await cache_service.get("health_check_test", default=None) is not None
            cache_status = {
                "status": "operational" if cache_service._connected else "unavailable",
                "connected": cache_service._connected
            }
            health_status["services"]["cache"] = cache_status
        except Exception as e:
            logger.error(f"Cache service health check failed: {str(e)}")
            health_status["services"]["cache"] = {"status": "error", "error": str(e)}
            health_status["overall_status"] = "degraded"

        # 检查GPU服务
        try:
            gpu_manager_service._scan_gpus()
            gpu_status = {
                "status": "operational" if gpu_manager_service._initialized else "unavailable",
                "gpus_available": len(gpu_manager_service.get_gpu_status()),
                "statistics": gpu_manager_service.get_gpu_statistics()
            }
            health_status["services"]["gpu"] = gpu_status
        except Exception as e:
            logger.error(f"GPU service health check failed: {str(e)}")
            health_status["services"]["gpu"] = {"status": "error", "error": str(e)}
            health_status["overall_status"] = "degraded"

        # 检查算法服务连接
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.ALGORITHM_SERVICE_URL}/health")
                algorithm_status = {
                    "status": "operational" if response.status_code == 200 else "unavailable",
                    "response_time_ms": 0  # We could measure this if needed
                }
                health_status["services"]["algorithm"] = algorithm_status
        except Exception as e:
            logger.error(f"Algorithm service health check failed: {str(e)}")
            health_status["services"]["algorithm"] = {"status": "error", "error": str(e)}
            health_status["overall_status"] = "degraded"

        return health_status

    async def get_detailed_health(self) -> Dict[str, Any]:
        """获取详细健康状态"""
        system_health = self.get_system_health()
        service_health = await self.get_service_health()
        
        detailed_health = {
            **system_health,
            "services": service_health["services"],
            "overall_status": service_health["overall_status"]
        }
        
        return detailed_health

    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康状态摘要"""
        system_info = self.get_system_health()
        
        return {
            "status": system_info["status"],
            "timestamp": system_info["timestamp"],
            "uptime": system_info["uptime"],
            "cpu_percent": system_info["system"]["cpu_percent"],
            "memory_percent": system_info["system"]["memory_percent"],
            "disk_percent": system_info["system"]["disk_percent"]
        }


# 全局健康检查服务实例
health_check_service = HealthCheckService()