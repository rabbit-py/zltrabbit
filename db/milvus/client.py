# -*- coding: utf-8 -*-
import copy
from uuid import uuid4

from loguru import logger
from base.di.service_location import BaseService
from pymilvus import db, connections, Collection, utility


class MilvusClient(BaseService):
    def __init__(self) -> None:
        self.client = None

    def get_client(self) -> Collection:
        if self.client is None:
            args = copy.deepcopy(self.__dict__)
            args.pop("client")
            alias = args.pop("alias", uuid4().hex)
            db_name = args.pop("db_name", "default")
            try:
                connections.connect(alias=alias, **args)
            except Exception as e:
                logger.error(e)
                raise e

            if utility.has_collection(self.collection_name, using=alias):
                collection = Collection(
                    db_name,
                    using=alias,
                )
            else:
                dbs = db.list_database()
                if db_name not in dbs:
                    db.create_database(db_name)
                connections.connect(alias=alias, db_name=db_name, **args)
                collection = Collection(db_name, using=alias)
            collection.load(_async=True)
            utility.wait_for_loading_complete(self.coll, using=self._conn.alias)
            db.using_database(db_name=db_name, using=alias)
            connections._fetch_handler(alias=alias)
            self.client = collection
        return self.client
