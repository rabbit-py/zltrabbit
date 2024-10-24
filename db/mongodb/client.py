# -*- coding: utf-8 -*-
import copy
from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient
from base.coroutine.shared import shared
from base.di.service_location import BaseService
from base.util.wraps import event
from db.mongodb.events import sshforward_event


class MongodbClient(BaseService):
    def __init__(self) -> None:
        self.client = None

    async def get_client(self) -> AsyncGenerator:
        if self.client is None:

            @shared(self.__dict__.get('url'))
            @event(sshforward_event, param=self.__dict__)
            async def run() -> AsyncGenerator:
                args = copy.deepcopy(self.__dict__)
                url = args.pop('url')
                args.pop('client', None)
                return AsyncIOMotorClient(url, **args)

            self.client = await run()
        return self.client
