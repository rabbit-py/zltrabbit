# -*- coding: utf-8 -*-
import redis.asyncio as redis


class RedisManager:

    @property
    def client(self) -> redis.Redis:
        return self._redis

    def __init__(self, url: str, config: dict = {}) -> None:
        self._redis = redis.from_url(url, **config)
