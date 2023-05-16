# -*- coding: utf-8 -*-

import json
from web.auth.storage_interface import StorageInterface
from base.di.service_location import service


class RedisStorage(StorageInterface):

    def __init__(self, name='redis.default') -> None:
        self._redis = service.get(name)

    async def save_token(self, token: dict, key: str = 'id', expired: int = 7200) -> bool:
        key = token.get('id')
        if not key:
            raise Exception("找不到key")
        client = await self._redis.client
        return await client.setex(key, expired, json.dumps(token, ensure_ascii=False))

    async def check_token(self, token: dict, expired: int = 24 * 60 * 60, key: str = 'id') -> bool:
        key = token.get('id')
        if not key:
            raise Exception("找不到key")
        client = await self._redis.client
        return await client.expire(key, expired)

    async def del_token(self, token: str, key: str = 'id') -> None:
        key = token.get('id')
        if not key:
            raise Exception("找不到key")
        client = await self._redis.client
        await client.delete(key)
