# -*- coding: utf-8 -*-

import asyncio
from functools import wraps
from loguru import logger
import inspect
from typing import Awaitable, Callable
from base.types import P, R


def retry(times=3, raise_except=True) -> Callable[P, Awaitable[R]]:

    def wrapper(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:

        @wraps(func)
        async def wrapper_function(*args: P.args, **kwargs: P.kwargs) -> R:
            nonlocal times
            while times > 0:
                try:
                    return (await func(*args, **kwargs)) if inspect.iscoroutinefunction(func) else func(*args, **kwargs)
                except Exception as e:
                    times -= 1
                    if times == 0:
                        if raise_except:
                            raise e
                        else:
                            logger.error(e)
                            return None
                    logger.warning(f'{func.__name__} retry the {str(times)} times')

        return wrapper_function

    return wrapper


def async_no_wait(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:

    @wraps(func)
    async def wrapper_function(*args: P.args, **kwargs: P.kwargs) -> R:
        logger.info(f'running task {func.__name__}')
        asyncio.ensure_future(func(*args, **kwargs))

    return wrapper_function