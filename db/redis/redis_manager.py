# -*- coding: utf-8 -*-
from functools import wraps
from redis.asyncio.client import AbstractRedis
from redis.asyncio.cluster import AbstractRedisCluster
from typing import (Any, Awaitable, Callable, Union, Optional, Tuple)
from loguru import logger
from redis import asyncio as aioredis
from redis.asyncio.lock import Lock
from base.di.service_location import BaseService, service
from base.types import P, R
from ..cache_helper import CacheInterface


class RedisManager(BaseService):

    @property
    def client(self) -> Union[AbstractRedis, AbstractRedisCluster]:
        return self.redis

    def __init__(self, url: str, config: dict = {}) -> None:
        self.redis = aioredis.from_url(url, **config)


class RedisCache(CacheInterface):

    def __init__(self, redis: Union[AbstractRedis, AbstractRedisCluster], prefix: str = 'cache') -> None:
        self.redis = redis
        self.prefix = prefix
        self.is_cluster = isinstance(redis, AbstractRedisCluster)

    async def get_with_ttl(self, key: str) -> Tuple[int, Optional[bytes]]:
        key = f"{self.prefix}:{key}"
        async with self.redis.pipeline(transaction=not self.is_cluster) as pipe:
            return await pipe.ttl(key).get(key).execute()

    async def get(self, key: str) -> Optional[bytes]:
        return await self.redis.get(f"{self.prefix}:{key}")

    async def set(self, key: str, value: Any, expire: Optional[float] = None) -> None:
        await self.redis.set(f"{self.prefix}:{key}", value, ex=expire or None)

    async def delete(self, key: str) -> Optional[int]:
        return await self.redis.delete(f"{self.prefix}:{key}")


def redis_lock(key: Any, name: str = 'redis.default', timeout: float = 10) -> Callable[P, Awaitable[R]]:

    def wrapper(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:

        @wraps(func)
        async def wrapper_function(*args: P.args, **kwargs: P.kwargs) -> R:
            async with Lock(service.get(name).client, key, timeout=timeout):
                logger.info('redis_lock: %s' % key)
                return await func(*args, **kwargs)

        return wrapper_function

    return wrapper
