# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
import asyncio
from functools import wraps
import time
from typing import (Any, Awaitable, Callable, Optional, Tuple)
from loguru import logger
from base.coroutine.shared import shared, key_builder
from base.di.service_location import service
from base.coder.coder_interface import CoderInterface
from base.coder.json_coder import ORJSONCoder
from base.types import P, R


class CacheInterface(metaclass=ABCMeta):

    @abstractmethod
    async def get_with_ttl(self, key: str) -> Tuple[int, Optional[bytes]]:
        pass

    @abstractmethod
    async def get(self, key: str) -> Optional[bytes]:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, expire: Optional[float] = None) -> None:
        pass

    @abstractmethod
    async def delete(self, key: str) -> Optional[int]:
        pass


class MemoryCache(CacheInterface):
    cache_map: dict = {}

    async def get_with_ttl(self, key: str) -> Tuple[int, Optional[bytes]]:
        result = MemoryCache.cache_map.get(key, None)
        if result is None:
            return 0, result
        ttl, set_time, value = result
        return set_time + ttl - int(time.time()) if ttl > 0 else ttl, value

    async def get(self, key: str) -> Optional[bytes]:
        _, _, result = MemoryCache.cache_map.get(key, None)
        return result

    async def set(self, key: str, value: Any, expire: Optional[float] = None) -> None:
        MemoryCache.cache_map[key] = (expire or 0, int(time.time()), value)
        if expire and expire > 0:

            async def ttl():
                await asyncio.sleep(expire)
                await self.delete(key)

            asyncio.get_running_loop().create_task(ttl())

    async def delete(self, key: str) -> Optional[int]:
        _, _, result = MemoryCache.cache_map.pop(key, None)
        if result:
            return 1
        return 0


def cache(key: Any = None,
          name: str = 'cache.default',
          expire: float = None,
          coder: CoderInterface = ORJSONCoder,
          prefix: str = '') -> Callable[P, Awaitable[R]]:

    def wrapper(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:

        @shared(coder=coder, prefix=prefix)
        @wraps(func)
        async def wrapper_function(*args: P.args, **kwargs: P.kwargs) -> R:
            new_key = key_builder(func, args, kwargs, key, coder, prefix)
            cache_obj = service.get(name)
            try:
                ttl, result = await cache_obj.get_with_ttl(new_key)
                result = coder.decode(result) if result is not None else None
            except Exception:
                logger.warning(
                    f"Error retrieving cache={name} key={str(new_key)}",
                    exc_info=True,
                )
                ttl, result = 0, None
            if result is None:
                result = await func(*args, **kwargs)
                try:
                    await cache_obj.set(new_key, coder.encode(result), expire)
                except Exception:
                    logger.warning(
                        f"Error setting cache={name} key={str(new_key)}",
                        exc_info=True,
                    )
            else:
                logger.info(f"Get key={str(new_key)} from Cache={name} ttl={ttl}")
            return result

        return wrapper_function

    return wrapper
