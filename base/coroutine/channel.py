# -*- coding: utf-8 -*-

import asyncio
from typing import Any


class Channel:

    @property
    def capacity(self) -> int:
        return self._queue.maxsize

    @property
    def length(self) -> int:
        return self._queue.qsize()

    @property
    def is_full(self) -> bool:
        return self._queue.full()

    @property
    def is_empty(self) -> bool:
        return self._queue.empty()

    def __init__(self, size: int = 1) -> None:
        self._queue = asyncio.Queue(maxsize=size)

    async def push(self, data: Any, timeout: float = None) -> Any:
        try:
            return await asyncio.wait_for(self._queue.put(data), timeout)
        except asyncio.TimeoutError:
            return False

    async def pop(self, timeout: float = None) -> Any:
        try:
            data = await asyncio.wait_for(self._queue.get(), timeout)
            self._queue.task_done()
        except asyncio.TimeoutError:
            return False
        return data