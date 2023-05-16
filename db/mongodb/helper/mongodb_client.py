# -*- coding: utf-8 -*-
import copy
import motor.motor_asyncio
from base.di.service_location import BaseService


class MongodbClient(BaseService):

    def __init__(self) -> None:
        self.client = None

    def get_client(self):
        if self.client is None:
            args = copy.deepcopy(self.__dict__)
            args.pop('client')
            self.client = motor.motor_asyncio.AsyncIOMotorClient(args.pop('url'), *args)
        return self.client
