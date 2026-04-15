from typing import Dict, List, Optional, Tuple, Any
import subprocess
import psutil
import GPUtil
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.resources import ModelRegistry
from app.models.user import User
import json


logger = logging.getLogger(__name__)


class GPUStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    UNAVAILABLE = "unavailable"
    MAINTENANCE = "maintenance"


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class GPUInfo:
    id: int
    name: str
    total_memory: float  # MB
    used_memory: float   # MB
    memory_util: float   # percentage
    gpu_util: float      # percentage
    status: GPUStatus
    temperature: Optional[float] = None
    power_draw: Optional[float] = None  # Watts
    max_power: Optional[float] = None  # Max power limit
    compute_capability: Optional[str] = None


@dataclass
class TaskAssignment:
    task_id: str
    gpu_id: int
    user_id: str
    model_id: Optional[str] = None
    assigned_at: datetime = None
    estimated_duration: Optional[int] = None  # seconds
    priority: TaskPriority = TaskPriority.MEDIUM
    resource_requirements: Dict[str, Any] = None  # memory, compute requirements

    def __post_init__(self):
        if self.assigned_at is None:
            self.assigned_at = datetime.utcnow()
        if self.resource_requirements is None:
            self.resource_requirements = {}


@dataclass
class GPUAllocation:
    gpu_id: int
    allocated_memory: float  # MB
    allocated_compute: float  # percentage
    task_ids: List[str]


class GPUManagerService:
    def __init__(self, db_session: Optional[Session] = None):
        self.gpus: List[GPUInfo] = []
        self.task_assignments: Dict[str, TaskAssignment] = {}
        self.gpu_allocations: Dict[int, GPUAllocation] = {}
        self._initialized = False
        self.db_session = db_session
        self._lock = asyncio.Lock()  # 用于并发安全

    async def initialize(self):
        """初始化GPU管理器"""
        async with self._lock:
            try:
                self._scan_gpus()
                self._initialize_allocations()
                self._initialized = True
                logger.info(f"Initialized GPU manager with {len(self.gpus)} GPUs")
            except Exception as e:
                logger.error(f"Failed to initialize GPU manager: {str(e)}")
                self._initialized = False

    def _initialize_allocations(self):
        """初始化GPU分配记录"""
        for gpu in self.gpus:
            self.gpu_allocations[gpu.id] = GPUAllocation(
                gpu_id=gpu.id,
                allocated_memory=0,
                allocated_compute=0,
                task_ids=[]
            )

    def _scan_gpus(self):
        """扫描可用GPU"""
        try:
            gpus = GPUtil.getGPUs()
            self.gpus = []
            
            for gpu in gpus:
                # 获取额外的GPU信息
                temperature = self._get_gpu_temperature(gpu.id)
                power_info = self._get_gpu_power_info(gpu.id)
                
                gpu_info = GPUInfo(
                    id=gpu.id,
                    name=gpu.name,
                    total_memory=gpu.memoryTotal,
                    used_memory=gpu.memoryUsed,
                    memory_util=gpu.memoryUtil * 100,
                    gpu_util=gpu.load * 100,
                    status=GPUStatus.BUSY if gpu.load > 0.1 else GPUStatus.IDLE,
                    temperature=temperature,
                    power_draw=power_info.get('power_draw'),
                    max_power=power_info.get('max_power'),
                    compute_capability=self._get_compute_capability(gpu.id)
                )
                self.gpus.append(gpu_info)
        except Exception as e:
            logger.error(f"Error scanning GPUs: {str(e)}")
            # 如果GPUtil失败，创建虚拟GPU信息用于测试
            self.gpus = [
                GPUInfo(
                    id=0,
                    name="Virtual GPU",
                    total_memory=8192,
                    used_memory=0,
                    memory_util=0,
                    gpu_util=0,
                    status=GPUStatus.IDLE
                )
            ]

    def _get_gpu_temperature(self, gpu_id: int) -> Optional[float]:
        """获取GPU温度"""
        try:
            result = subprocess.run(['nvidia-smi', f'--id={gpu_id}', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                temp = result.stdout.strip()
                if temp and temp != '[Not Supported]':
                    return float(temp)
        except:
            pass
        return None

    def _get_gpu_power_info(self, gpu_id: int) -> Dict[str, Optional[float]]:
        """获取GPU功耗信息"""
        try:
            result = subprocess.run(['nvidia-smi', f'--id={gpu_id}', '--query-gpu=power.draw,power.limit', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                parts = result.stdout.strip().split(', ')
                if len(parts) == 2:
                    power_draw = float(parts[0].replace(' W', '')) if parts[0] != '[Not Supported]' else None
                    max_power = float(parts[1].replace(' W', '')) if parts[1] != '[Not Supported]' else None
                    return {'power_draw': power_draw, 'max_power': max_power}
        except:
            pass
        return {'power_draw': None, 'max_power': None}

    def _get_compute_capability(self, gpu_id: int) -> Optional[str]:
        """获取GPU计算能力"""
        # 这里可以实现获取计算能力的逻辑
        return None

    def get_gpu_status(self) -> List[GPUInfo]:
        """获取GPU状态"""
        self._scan_gpus()  # 每次获取状态时都重新扫描
        return self.gpus

    def get_available_gpu(self, min_memory_required: float = 0, priority: TaskPriority = TaskPriority.MEDIUM) -> Optional[int]:
        """获取满足条件的可用GPU ID"""
        self._scan_gpus()
        
        # 首先寻找完全空闲且满足内存要求的GPU
        for gpu in self.gpus:
            allocation = self.gpu_allocations.get(gpu.id)
            if allocation and gpu.status == GPUStatus.IDLE:
                available_memory = gpu.total_memory - allocation.allocated_memory
                if available_memory >= min_memory_required:
                    return gpu.id
        
        # 如果没有完全空闲的，寻找负载较低且满足要求的GPU
        for gpu in sorted(self.gpus, key=lambda x: x.gpu_util):  # 按使用率排序
            allocation = self.gpu_allocations.get(gpu.id)
            if allocation:
                available_memory = gpu.total_memory - allocation.allocated_memory
                if (gpu.gpu_util < 80 and available_memory >= min_memory_required and 
                    len(allocation.task_ids) < 3):  # 限制每个GPU最多运行3个任务
                    return gpu.id
        
        return None

    async def assign_task_to_gpu(
        self, 
        task_id: str, 
        user_id: str, 
        model_id: Optional[str] = None,
        estimated_duration: Optional[int] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        resource_requirements: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """为任务分配GPU"""
        if not self._initialized:
            await self.initialize()
        
        if resource_requirements is None:
            resource_requirements = {"min_memory_mb": 1024}  # 默认1GB
        
        min_memory = resource_requirements.get("min_memory_mb", 1024)
        
        async with self._lock:
            gpu_id = self.get_available_gpu(min_memory, priority)
            if gpu_id is not None:
                assignment = TaskAssignment(
                    task_id=task_id,
                    gpu_id=gpu_id,
                    user_id=user_id,
                    model_id=model_id,
                    estimated_duration=estimated_duration,
                    priority=priority,
                    resource_requirements=resource_requirements
                )
                
                self.task_assignments[task_id] = assignment
                
                # 更新GPU分配
                allocation = self.gpu_allocations[gpu_id]
                allocation.task_ids.append(task_id)
                allocation.allocated_memory += min_memory
                
                logger.info(f"Assigned task {task_id} to GPU {gpu_id} for user {user_id}")
                return gpu_id
        
        logger.warning(f"No available GPU for task {task_id}")
        return None

    async def release_gpu(self, task_id: str):
        """释放GPU"""
        async with self._lock:
            if task_id in self.task_assignments:
                assignment = self.task_assignments[task_id]
                gpu_id = assignment.gpu_id
                
                # 从分配中移除
                if gpu_id in self.gpu_allocations:
                    allocation = self.gpu_allocations[gpu_id]
                    if task_id in allocation.task_ids:
                        allocation.task_ids.remove(task_id)
                    
                    # 减少分配的内存（这里简化处理，实际应该根据任务实际使用的内存来减少）
                    min_memory = assignment.resource_requirements.get("min_memory_mb", 1024)
                    allocation.allocated_memory = max(0, allocation.allocated_memory - min_memory)
                
                # 从任务分配中移除
                del self.task_assignments[task_id]
                
                logger.info(f"Released GPU {gpu_id} from task {task_id}")

    def get_task_assignment(self, task_id: str) -> Optional[TaskAssignment]:
        """获取任务的GPU分配信息"""
        return self.task_assignments.get(task_id)

    def get_gpu_utilization(self) -> Dict[int, float]:
        """获取各GPU的利用率"""
        self._scan_gpus()
        return {gpu.id: gpu.gpu_util for gpu in self.gpus}

    def get_system_resources(self) -> Dict[str, float]:
        """获取系统资源信息"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "memory_total_gb": memory.total / (1024**3)
        }

    async def run_gpu_task(
        self, 
        task_func, 
        task_id: str, 
        user_id: str,
        model_id: Optional[str] = None,
        *args, 
        gpu_id: Optional[int] = None, 
        **kwargs
    ):
        """在指定GPU上运行任务"""
        if gpu_id is None:
            # 自动分配GPU
            gpu_id = await self.assign_task_to_gpu(task_id, user_id, model_id)
            if gpu_id is None:
                raise RuntimeError("No available GPU for task")
        
        # 设置CUDA_VISIBLE_DEVICES环境变量
        import os
        original_cuda_devices = os.environ.get('CUDA_VISIBLE_DEVICES')
        os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_id)
        
        try:
            # 运行任务
            result = await task_func(*args, **kwargs) if asyncio.iscoroutinefunction(task_func) else task_func(*args, **kwargs)
            return result
        finally:
            # 恢复原始环境变量
            if original_cuda_devices is not None:
                os.environ['CUDA_VISIBLE_DEVICES'] = original_cuda_devices
            else:
                os.environ.pop('CUDA_VISIBLE_DEVICES', None)
            
            # 释放GPU
            await self.release_gpu(task_id)

    def get_gpu_statistics(self) -> Dict:
        """获取GPU统计信息"""
        gpus = self.get_gpu_status()
        
        if not gpus:
            return {
                "total_gpus": 0,
                "available_gpus": 0,
                "avg_gpu_util": 0,
                "avg_memory_util": 0,
                "total_memory_mb": 0,
                "used_memory_mb": 0
            }
        
        total_gpus = len(gpus)
        available_gpus = sum(1 for gpu in gpus if gpu.status == GPUStatus.IDLE)
        avg_gpu_util = sum(gpu.gpu_util for gpu in gpus) / total_gpus
        avg_memory_util = sum(gpu.memory_util for gpu in gpus) / total_gpus
        total_memory = sum(gpu.total_memory for gpu in gpus)
        used_memory = sum(gpu.used_memory for gpu in gpus)
        
        return {
            "total_gpus": total_gpus,
            "available_gpus": available_gpus,
            "avg_gpu_util": round(avg_gpu_util, 2),
            "avg_memory_util": round(avg_memory_util, 2),
            "total_memory_mb": total_memory,
            "used_memory_mb": used_memory,
            "allocations": {gpu.id: len(self.gpu_allocations.get(gpu.id, GPUAllocation(gpu.id, 0, 0, [])).task_ids) 
                           for gpu in gpus}
        }

    def get_user_gpu_usage(self, user_id: str) -> Dict[str, Any]:
        """获取用户的GPU使用情况"""
        user_tasks = [assignment for assignment in self.task_assignments.values() 
                     if assignment.user_id == user_id]
        
        gpu_usage = {}
        for task in user_tasks:
            gpu_id = task.gpu_id
            if gpu_id not in gpu_usage:
                gpu_usage[gpu_id] = {
                    "tasks": [],
                    "total_estimated_time": 0,
                    "priority_tasks": 0
                }
            
            gpu_usage[gpu_id]["tasks"].append(task.task_id)
            if task.estimated_duration:
                gpu_usage[gpu_id]["total_estimated_time"] += task.estimated_duration
            if task.priority == TaskPriority.HIGH or task.priority == TaskPriority.CRITICAL:
                gpu_usage[gpu_id]["priority_tasks"] += 1
        
        return {
            "user_id": user_id,
            "active_tasks": len(user_tasks),
            "gpu_usage": gpu_usage
        }

    async def set_gpu_maintenance_mode(self, gpu_id: int, maintenance: bool):
        """设置GPU维护模式"""
        async with self._lock:
            for gpu in self.gpus:
                if gpu.id == gpu_id:
                    gpu.status = GPUStatus.MAINTENANCE if maintenance else GPUStatus.IDLE
                    logger.info(f"Set GPU {gpu_id} to {'MAINTENANCE' if maintenance else 'IDLE'} mode")
                    break

    def get_gpu_allocation_details(self) -> Dict[int, Dict[str, Any]]:
        """获取GPU分配详情"""
        details = {}
        for gpu_id, allocation in self.gpu_allocations.items():
            gpu_info = next((gpu for gpu in self.gpus if gpu.id == gpu_id), None)
            if gpu_info:
                details[gpu_id] = {
                    "gpu_info": gpu_info,
                    "allocation": allocation,
                    "remaining_memory_mb": gpu_info.total_memory - allocation.allocated_memory,
                    "task_count": len(allocation.task_ids)
                }
        return details


# 全局GPU管理服务实例
gpu_manager_service = GPUManagerService()