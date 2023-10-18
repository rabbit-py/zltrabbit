# -*- coding: utf-8 -*-
import copy
from motor.motor_asyncio import AsyncIOMotorClient
from base.di.service_location import BaseService
from base.util.wraps import event
from db.mongodb.events import sshforward_event


class MongodbClient(BaseService):
    def __init__(self) -> None:
        self.client = None

    async def get_client(self) -> AsyncIOMotorClient:
        @event(sshforward_event, param=self.__dict__)
        async def run() -> AsyncIOMotorClient:
            if self.client is None:
                args = copy.deepcopy(self.__dict__)
                url = args.pop('url')
                args.pop('client', None)
                self.client = AsyncIOMotorClient(url, **args)
            return self.client

        return await run()
