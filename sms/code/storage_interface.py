# -*- coding: utf-8 -*-

import abc


class StorageInterface(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def save(self, platform: str, username: str, code: str, expire: int = 300) -> bool:
        pass

    async def get(self, platform: str, username: str) -> int:
        pass