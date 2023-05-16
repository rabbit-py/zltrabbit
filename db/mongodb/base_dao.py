# -*- coding: utf-8 -*-

from db.mongodb.common_da_helper import CommonDAHelper


class BaseDAO:

    def __init__(self, db: str, conn: str) -> None:
        self._db = db
        self._conn = conn
        self._db_map = {}

    def __getattr__(self, key: str) -> CommonDAHelper:
        key = key.replace('_db', '')
        if key not in self._db_map:
            self._db_map[key] = CommonDAHelper(self._db, key, self._conn)
        return self._db_map[key]