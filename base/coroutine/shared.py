# -*- coding: utf-8 -*-

from functools import wraps
from hashlib import md5
from typing import (Any, Awaitable, Callable)
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


def shared(key: Any, timeout: float = 3, coder: CoderInterface = ORJSONCoder) -> Callable[P, Awaitable[R]]:

    def wrapper(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:

        @wraps(func)
        async def wrapper_function(*args: P.args, **kwargs: P.kwargs) -> R:
            new_key = coder.encode(key).decode()
            if '.' in new_key or len(new_key) > 32:
                new_key = md5(new_key.encode("utf-8")).hexdigest()
            shared_obj = Share.get_share(new_key)
            try:
                await shared_obj.channel.push(new_key, timeout)
                if Share.share_map.get(new_key) is None:
                    return shared_obj.result
                shared_obj.data = await func(*args, **kwargs)
                return shared_obj.result
            except Exception as e:
                raise e
            finally:
                if not shared_obj.channel.is_empty:
                    await shared_obj.channel.pop(timeout)
                Share.share_map.pop(new_key, None)

        return wrapper_function

    return wrapper