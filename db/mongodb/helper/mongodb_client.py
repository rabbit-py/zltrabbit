# -*- coding: utf-8 -*-
import copy
from motor.motor_asyncio import AsyncIOMotorClient
from base.di.service_location import BaseService


class MongodbClient(BaseService):
    def __init__(self) -> None:
        self.client = None

    def get_client(self) -> AsyncIOMotorClient:
        if self.client is None:
            args = copy.deepcopy(self.__dict__)
            args.pop('client')
            self.client = AsyncIOMotorClient(args.pop('url'), **args)
        return self.client
