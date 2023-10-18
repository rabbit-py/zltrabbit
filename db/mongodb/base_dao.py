# -*- coding: utf-8 -*-

import asyncio
from base.di.service_location import service
from db.mongodb.common_da_helper import CommonDAHelper
from motor.motor_asyncio import AsyncIOMotorClient
from base.coroutine.context import context

class BaseDAO:
    def __init__(self, db: str, conn: str) -> None:
        self._db = db
        self._conn = conn
        self._db_map = {}

    @property
    async def client(self) -> AsyncIOMotorClient:
        return await service.get(self._conn).get_client()

    async def transaction(self, *args, use_session=True, **kwargs) -> list:
        async with await self.client.start_session(causal_consistency=True) as session:
            async with session.start_transaction():
                try:
                    use_session and context.set('mongo_session', session)
                    return await asyncio.gather(*args, **kwargs)
                except Exception as e:
                    raise e
                finally:
                    use_session and context.remove('mongo_session')

    def __getattr__(self, key: str) -> CommonDAHelper:
        key = key.replace('_db', '')
        if key not in self._db_map:
            self._db_map[key] = CommonDAHelper(self._db, key, self._conn)
        return self._db_map[key]
