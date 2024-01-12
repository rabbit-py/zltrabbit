# -*- coding: utf-8 -*-

from functools import wraps
from hashlib import md5
import inspect
from typing import Any, Awaitable, Callable
from base.coder.coder_interface import CoderInterface
from base.coder.json_coder import ORJSONCoder
from base.di.service_location import BaseService
from .channel import Channel
from ..types import P, R


class Share(BaseService):
    share_map: dict = {}

    @property
    def result(self) -> Any:
        return self.data

    def __init__(self) -> None:
        self.channel = Channel()

    @classmethod
    def get_share(self, key: str) -> "Share":
        obj = self.share_map.get(key)
        if not obj:
            obj = Share()
            self.share_map[key] = obj
        return obj


def key_builder(
    func: Callable[P, Awaitable[R]],
    args: list,
    kwargs: dict,
    key: Any = None,
    coder: CoderInterface = ORJSONCoder,
    prefix: str = '',
) -> str:
    ordered_kwargs = sorted(kwargs.items())
    sig = inspect.signature(func)
    tmp_param = (
        (func.__module__ or "")
        + '.'
        + func.__name__
        + str(args[1:] if 'self' in sig.parameters else args)
        + str(ordered_kwargs)
    )
    return with_key_builder(key or tmp_param, coder, prefix)


def with_key_builder(key: Any = None, coder: CoderInterface = ORJSONCoder, prefix: str = '') -> str:
    new_key = key if key and isinstance(key, str) else coder.encode(key).decode()
    if '.' in new_key or len(new_key) > 32:
        new_key = md5(new_key.encode("utf-8")).hexdigest()
    return f'{prefix}:{new_key}' if prefix else new_key


def shared(
    key: Any = None, timeout: float = 3, coder: CoderInterface = ORJSONCoder, prefix: str = '', only_lock=False
) -> Callable[P, Awaitable[R]]:
    def wrapper(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def wrapper_function(*args: P.args, **kwargs: P.kwargs) -> R:
            new_key = key_builder(func, args, kwargs, key, coder, prefix)
            shared_obj = Share.get_share(new_key)
            try:
                await shared_obj.channel.push(new_key, timeout)
                if Share.share_map.get(new_key) is None and not only_lock:
                    return shared_obj.result
                shared_obj.data = (await func(*args, **kwargs)) if inspect.iscoroutinefunction(func) else func(*args, **kwargs)
                return shared_obj.result
            except Exception as e:
                raise e
            finally:
                if not shared_obj.channel.is_empty:
                    await shared_obj.channel.pop(timeout)
                Share.share_map.pop(new_key, None)

        return wrapper_function

    return wrapper
