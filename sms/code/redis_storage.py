# -*- coding: utf-8 -*-

from .storage_interface import StorageInterface
from base.di.service_location import service


class RedisStorage(StorageInterface):

    def __init__(self, name='redis.default') -> None:
        super().__init__()
        self._redis = service.get(name)

    async def save(self, platform: str, username: str, code: str, expire: int = 300) -> bool:
        client = await self._redis.client
        return await client.set(f'sms:{platform}:{username}', code, ex=expire)

    async def get(self, platform: str, username: str) -> str:
        client = await self._redis.client
        return await client.get(f'sms:{platform}:{username}')
