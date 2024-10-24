# -*- coding: utf-8 -*-

from typing import AsyncGenerator
from base.di.service_location import service
from pymilvus import connections

from db.milvus.common_da_helpger import CommonDAHelper


class BaseDAO:
    def __init__(self, db: str, conn: str) -> None:
        self._db = db
        self._conn = conn
        self._db_map = {}

    @property
    def client(self) -> AsyncGenerator:
        return service.get(self._conn).get_client()

    def __getattr__(self, key: str) -> CommonDAHelper:
        key = key.replace("_db", "")
        if key not in self._db_map:
            self._db_map[key] = CommonDAHelper(self._db, key, self._conn)
        return self._db_map[key]
