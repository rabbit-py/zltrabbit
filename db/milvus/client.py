# -*- coding: utf-8 -*-
import copy
from base.di.service_location import BaseService
from pymilvus import db, connections, Collection


class MilvusClient(BaseService):
    def __init__(self) -> None:
        self.client = None

    async def get_client(self) -> Collection:
        if self.client is None:
            args = copy.deepcopy(self.__dict__)
            args.pop("client")
            alias = args.get("alias", "default")
            db_name = args.get("db_name", "default")
            connections.connect(**args)
            dbs = db.list_database(using=alias)
            if db_name not in dbs:
                db.create_database(db_name)
            db.using_database(db_name=db_name, using=alias)
            connections._fetch_handler(alias=alias)
            self.client = Collection
        return self.client
