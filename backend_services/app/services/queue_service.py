from typing import Dict, Any, Optional, Callable
import asyncio
import uuid
from enum import Enum
from datetime import datetime
from dataclasses import dataclass
import logging


logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    id: str
    name: str
    func: Callable
    args: tuple
    kwargs: dict
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    user_id: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class QueueService:
    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.task_queue = asyncio.Queue()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_registry: Dict[str, Task] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.running = False

    async def start(self):
        """启动队列服务"""
        self.running = True
        # 启动工作协程
        for _ in range(min(5, self.max_concurrent_tasks)):
            asyncio.create_task(self._worker())

    async def stop(self):
        """停止队列服务"""
        self.running = False
        # 取消所有活跃任务
        for task_id, task_obj in self.active_tasks.items():
            if not task_obj.done():
                task_obj.cancel()
        
        # 等待所有任务完成
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)

    async def _worker(self):
        """工作协程，处理队列中的任务"""
        while self.running:
            try:
                task_id = await self.task_queue.get()
                if task_id in self.task_registry:
                    await self._execute_task(task_id)
                self.task_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")

    async def _execute_task(self, task_id: str):
        """执行单个任务"""
        task = self.task_registry.get(task_id)
        if not task:
            return

        try:
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            
            # 使用信号量限制并发
            async with self.semaphore:
                if task_id in self.active_tasks and self.active_tasks[task_id].cancelled():
                    task.status = TaskStatus.CANCELLED
                    return

                # 执行任务
                result = await task.func(*task.args, **task.kwargs)
                
                # 更新任务状态
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                
        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.utcnow()
        finally:
            # 从活跃任务中移除
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

    async def submit_task(self, func: Callable, *args, user_id: Optional[str] = None, **kwargs) -> str:
        """提交新任务到队列"""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            name=f"{func.__name__}_{task_id}",
            func=func,
            args=args,
            kwargs=kwargs,
            user_id=user_id
        )
        
        self.task_registry[task_id] = task
        await self.task_queue.put(task_id)
        
        # 创建一个异步任务来跟踪这个任务
        self.active_tasks[task_id] = asyncio.current_task()
        
        logger.info(f"Submitted task {task_id} to queue")
        return task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务状态"""
        return self.task_registry.get(task_id)

    def get_user_tasks(self, user_id: str) -> list:
        """获取用户的所有任务"""
        return [task for task in self.task_registry.values() if task.user_id == user_id]

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
            task = self.task_registry.get(task_id)
            if task:
                task.status = TaskStatus.CANCELLED
            return True
        return False

    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self.task_queue.qsize()

    def get_active_task_count(self) -> int:
        """获取活跃任务数量"""
        return len([task for task in self.active_tasks.values() if not task.done()])


# 全局队列服务实例
queue_service = QueueService()