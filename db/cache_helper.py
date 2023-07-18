# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from functools import wraps
from hashlib import md5
from typing import (Any, Awaitable, Callable, Optional, Tuple)
from loguru import logger
from base.coroutine.shared import shared
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


def cache(key: Any, name: str = 'cache.default', expire: float = None, coder: CoderInterface = ORJSONCoder) -> Callable[P, Awaitable[R]]:

    def wrapper(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:

        @wraps(func)
        @shared(key=key, coder=coder)
        async def wrapper_function(*args: P.args, **kwargs: P.kwargs) -> R:
            cache_obj = service.get(name)
            new_key = coder.encode(key).decode()
            if '.' in new_key or len(new_key) > 32:
                new_key = md5(new_key.encode("utf-8")).hexdigest()
            try:
                ttl, result = await cache_obj.get_with_ttl(new_key)
                result = coder.decode(result) if result is not None else None
            except Exception:
                logger.warning(
                    f"Error retrieving cache key={str(new_key)}",
                    exc_info=True,
                )
                ttl, result = 0, None
            if result is None:
                result = await func(*args, **kwargs)
                try:
                    await cache_obj.set(new_key, coder.encode(result), expire)
                except Exception:
                    logger.warning(
                        f"Error setting cache key={str(new_key)}",
                        exc_info=True,
                    )
            else:
                logger.info(f"Get key={str(new_key)} from Cache ttl={ttl}")
            return result

        return wrapper_function

    return wrapper
