# -*- coding: utf-8 -*-

from abc import ABCMeta
from ..di.service_location import service
from typing import Any


class Pool:

    def __init__(self, module: str, config: dict, size: int = 10) -> None:
        self._total = 0
        self._module = module
        self._config = config
        self._pool = service.create('common.util.channel.Channel', {"size": size}, False)

    async def get(self, timeout: float = None) -> object:
        if self._pool.is_empty and self._pool.capacity == 0 or self._total < self._pool.capacity:
            self._total += 1
            self._pool.push(service.create(self._module, self._config, False))
        return await self._pool.pop(timeout)

    async def release(self, item: Any) -> None:
        if not self._pool.is_full:
            await self._pool.push(item)

    def delete(self) -> int:
        self._total -= 1
        return self._total


class BasePoolObject(metaclass=ABCMeta):

    @property
    def pool(self) -> Pool:
        return self._pool

    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    def release(self) -> None:
        self._pool.release(self)