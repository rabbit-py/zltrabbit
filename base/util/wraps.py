# -*- coding: utf-8 -*-

import asyncio
from functools import wraps
from loguru import logger
import inspect
from typing import Awaitable, Callable
from base.types import P, R


class NotRetryException(Exception):
    ...


def retry(times: int = 3, sleep: float = 0.2, raise_except: bool = True) -> Callable[P, Awaitable[R]]:

    def wrapper(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:

        @wraps(func)
        async def wrapper_function(*args: P.args, **kwargs: P.kwargs) -> R:
            nonlocal times
            while times > 0:
                try:
                    return (await func(*args, **kwargs)) if inspect.iscoroutinefunction(func) else func(*args, **kwargs)
                except NotRetryException as e:
                    if raise_except:
                        raise e
                    else:
                        logger.error(e)
                        return None
                except Exception as e:
                    times -= 1
                    if times == 0:
                        if raise_except:
                            raise e
                        else:
                            logger.error(e)
                            return None
                logger.warning(
                    f'{func.__name__} retry the {str(times)} times with sleep {sleep}s')

                if sleep > 0:
                    asyncio.sleep(sleep)

        return wrapper_function

    return wrapper


def async_nowait(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:

    @wraps(func)
    async def wrapper_function(*args: P.args, **kwargs: P.kwargs) -> R:
        logger.info(f'running task {func.__name__}')
        asyncio.ensure_future(func(*args, **kwargs))

    return wrapper_function
