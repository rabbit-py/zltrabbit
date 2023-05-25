# -*- coding: utf-8 -*-

import asyncio
from base.di.service_location import service
from db.mongodb.common_da_helper import CommonDAHelper
from motor.motor_asyncio import AsyncIOMotorClient


class BaseDAO:

    def __init__(self, db: str, conn: str) -> None:
        self._db = db
        self._conn = conn
        self._db_map = {}

    @property
    def client(self) -> AsyncIOMotorClient:
        return service.get(self._conn).get_client()

    async def transaction(self, *args, **kwargs) -> bool:
        async with await self.client.start_session(causal_consistency=True) as session:
            async with session.start_transaction():
                await asyncio.gather(*args, **kwargs)
                return True

    def __getattr__(self, key: str) -> CommonDAHelper:
        key = key.replace('_db', '')
        if key not in self._db_map:
            self._db_map[key] = CommonDAHelper(self._db, key, self._conn)
        return self._db_map[key]