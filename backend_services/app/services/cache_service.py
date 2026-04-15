from typing import Any, Optional, Union
import redis.asyncio as redis
import json
import pickle
from config.settings import settings
import logging
from datetime import timedelta


logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._connected = False

    async def connect(self):
        """连接到Redis"""
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL)
            # 测试连接
            await self.redis_client.ping()
            self._connected = True
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self._connected = False

    async def disconnect(self):
        """断开Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            self._connected = False

    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """设置缓存值"""
        if not self._connected or not self.redis_client:
            return False

        try:
            # 序列化值
            serialized_value = self._serialize(value)
            result = await self.redis_client.set(key, serialized_value)
            
            # 设置过期时间
            if expire:
                await self.redis_client.expire(key, expire)
            
            return result
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {str(e)}")
            return False

    async def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        if not self._connected or not self.redis_client:
            return default

        try:
            value = await self.redis_client.get(key)
            if value is None:
                return default
            
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {str(e)}")
            return default

    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        if not self._connected or not self.redis_client:
            return False

        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._connected or not self.redis_client:
            return False

        try:
            result = await self.redis_client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to check existence of cache key {key}: {str(e)}")
            return False

    async def flush_all(self) -> bool:
        """清空所有缓存"""
        if not self._connected or not self.redis_client:
            return False

        try:
            await self.redis_client.flushall()
            return True
        except Exception as e:
            logger.error(f"Failed to flush cache: {str(e)}")
            return False

    async def ttl(self, key: str) -> int:
        """获取键的剩余生存时间"""
        if not self._connected or not self.redis_client:
            return -1

        try:
            result = await self.redis_client.ttl(key)
            return result
        except Exception as e:
            logger.error(f"Failed to get TTL for key {key}: {str(e)}")
            return -1

    def _serialize(self, value: Any) -> bytes:
        """序列化值"""
        # 尝试JSON序列化，如果失败则使用pickle
        try:
            return json.dumps(value).encode('utf-8')
        except (TypeError, ValueError):
            # 如果JSON序列化失败，使用pickle
            return pickle.dumps(value)

    def _deserialize(self, value: bytes) -> Any:
        """反序列化值"""
        # 尝试JSON反序列化，如果失败则使用pickle
        try:
            return json.loads(value.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            # 如果JSON反序列化失败，使用pickle
            return pickle.loads(value)

    async def increment(self, key: str, amount: int = 1) -> int:
        """递增计数器"""
        if not self._connected or not self.redis_client:
            return 0

        try:
            result = await self.redis_client.incrby(key, amount)
            return result
        except Exception as e:
            logger.error(f"Failed to increment counter {key}: {str(e)}")
            return 0

    async def decrement(self, key: str, amount: int = 1) -> int:
        """递减计数器"""
        if not self._connected or not self.redis_client:
            return 0

        try:
            result = await self.redis_client.decrby(key, amount)
            return result
        except Exception as e:
            logger.error(f"Failed to decrement counter {key}: {str(e)}")
            return 0

    async def set_add(self, key: str, *values) -> int:
        """向集合添加元素"""
        if not self._connected or not self.redis_client:
            return 0

        try:
            result = await self.redis_client.sadd(key, *values)
            return result
        except Exception as e:
            logger.error(f"Failed to add to set {key}: {str(e)}")
            return 0

    async def set_members(self, key: str) -> set:
        """获取集合所有成员"""
        if not self._connected or not self.redis_client:
            return set()

        try:
            result = await self.redis_client.smembers(key)
            return {self._deserialize(item) for item in result}
        except Exception as e:
            logger.error(f"Failed to get set members for {key}: {str(e)}")
            return set()


# 全局缓存服务实例
cache_service = CacheService()