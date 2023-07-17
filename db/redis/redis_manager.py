# -*- coding: utf-8 -*-
from functools import wraps
from loguru import logger
import redis.asyncio as redis
from redis.asyncio.lock import Lock
from base.di.service_location import BaseService, service


class RedisManager(BaseService):

    @property
    def client(self) -> redis.Redis:
        return self._redis

    def __init__(self, url: str, config: dict = {}) -> None:
        self._redis = redis.from_url(url, **config)


def redis_lock(name: str, key: str = 'redis.default', timeout: float = 10):

    def lock(func):

        @wraps(func)
        async def wrapper_function(*args, **kwargs):
            async with Lock(await service.get(key).client, name, timeout=timeout):
                logger.info('redis_lock: %s' % name)
                return await func(*args, **kwargs)

        return wrapper_function

    return lock
