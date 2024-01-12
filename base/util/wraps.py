# -*- coding: utf-8 -*-

import asyncio
from functools import wraps
from loguru import logger
import inspect
from typing import Awaitable, Callable, Union
from base.types import P, R


class NotRetryException(Exception):
    ...


def retry(times: int = 3, sleep: Union[float, list] = 0.2, raise_except: bool = True) -> Callable[P, Awaitable[R]]:
    def wrapper(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def wrapper_function(*args: P.args, **kwargs: P.kwargs) -> R:
            nonlocal times
            times = max(times, len(sleep) if isinstance(sleep, list) else 0) + 1
            num = times
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

                if isinstance(sleep, list) and len(sleep) > 0:
                    wait = sleep.pop(0)
                    logger.warning(f'{func.__name__} retry the {str(num-times)} times with sleep {wait}s')
                    await asyncio.sleep(wait)
                elif sleep > 0:
                    logger.warning(f'{func.__name__} retry the {str(num-times)} times with sleep {sleep}s')
                    await asyncio.sleep(sleep)

        return wrapper_function

    return wrapper


def async_nowait(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    @wraps(func)
    async def wrapper_function(*args: P.args, **kwargs: P.kwargs) -> R:
        logger.info(f'running task {func.__name__}')
        asyncio.ensure_future(func(*args, **kwargs))

    return wrapper_function


def event(
    before: Callable[P, Awaitable[R]] = None,
    after: Callable[P, Awaitable[R]] = None,
    reraise: bool = True,
    *event_args: P.args,
    **event_kwargs: P.kwargs,
) -> Callable[P, Awaitable[R]]:
    def wrapper(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def wrapper_function(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                if before:
                    ret = (
                        (await before(*event_args, **event_kwargs))
                        if inspect.iscoroutinefunction(before)
                        else before(*event_args, **event_kwargs)
                    )
                    params = func.__annotations__
                    if 'before_result' in params:
                        kwargs.update({'before_result': ret})
                ret = (await func(*args, **kwargs)) if inspect.iscoroutinefunction(func) else func(*args, **kwargs)
                if after:
                    ret = (
                        (await after(ret, *event_args, **event_kwargs))
                        if inspect.iscoroutinefunction(after)
                        else after(ret, *event_args, **event_kwargs)
                    )

                return ret
            except Exception as e:
                if reraise:
                    raise e
                else:
                    logger.exception(e)

        return wrapper_function

    return wrapper
