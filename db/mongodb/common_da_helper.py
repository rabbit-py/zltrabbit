# -*- coding: utf-8 -*-

from typing import Any, List, Union
from async_property import async_property

from pymongo import ReturnDocument, UpdateOne
from base.di.service_location import service
from base.coroutine.context import context
from motor.motor_asyncio import AsyncIOMotorClientSession, AsyncIOMotorCollection
from db.base_model import BaseModel
from db.cache_helper import cache

from db.da_interface import DaInterface


class CommonDAHelper(DaInterface):
    @property
    def session(self) -> AsyncIOMotorClientSession:
        return context.get('mongo_session')

    @async_property
    async def collection(self) -> AsyncIOMotorCollection:
        return (await service.get(self.name).get_client())[self.db][self.coll]

    def __init__(self, db: str, coll: str, name: str = 'db.default') -> None:
        self.name = name
        self.db = db
        self.coll = coll
        self.id_generator = service.id_generator

    async def updateAll(self, data: dict, matcher: dict) -> int:
        return (await (await self.collection).update_many(matcher, {'$set': data})).modified_count

    async def save(
        self, model: Union[BaseModel, dict], matcher: dict = None, projection: dict = {}, upsert: bool = True, more_update={}
    ) -> dict:
        if isinstance(model, dict):
            model = BaseModel().load(model)
        tmp = model.to_dict()
        data = model.data
        if matcher is None:
            matcher = {model.key: tmp.get(model.key)}
        projection.update({"_id": False})
        return await (await self.collection).find_one_and_update(
            matcher,
            dict(more_update, **{"$set": data, '$setOnInsert': dict(filter(lambda x: x[0] not in data, tmp.items()))}),
            return_document=ReturnDocument.AFTER,
            upsert=upsert,
            projection=projection,
            session=self.session,
        )

    async def batch_save(self, models: list[Union[BaseModel, dict]], matcher: list = None, upsert: bool = True) -> int:
        bulk_write_data = []
        for model in models:
            if isinstance(model, dict):
                model = BaseModel().load(model)
            tmp = model.to_dict()
            data = model.data
            if matcher is None:
                condition = {model.key: tmp.get(model.key)}
            else:
                condition = {}
                for key in matcher:
                    condition.update({key: data.get(key)})
            bulk_write_data.append(
                UpdateOne(
                    condition,
                    {"$set": data, '$setOnInsert': dict(filter(lambda x: x[0] not in data, tmp.items()))},
                    upsert=upsert,
                )
            )

        result = await (await self.collection).bulk_write(bulk_write_data, session=self.session)
        return result.inserted_count + result.modified_count

    async def get(self, id: Any = None, matcher: dict = {}, projection: dict = {}, sort: list = [], **kwargs) -> dict:
        if id:
            matcher.update({"id": id})
        if not matcher:
            return {}
        projection.update({"_id": False})
        return (await (await self.collection).find_one(matcher, projection=projection, sort=sort, **kwargs)) or {}

    async def list(
        self, matcher: dict = {}, projection: dict = {}, page: int = 1, page_size: int = 0, sort=[], **kwargs
    ) -> List:
        page = page if page > 0 else 1
        projection.update({"_id": False})
        return (
            await (await self.collection)
            .find(matcher, projection=projection, sort=sort, **kwargs)
            .skip(page_size * (page - 1))
            .limit(page_size)
            .to_list(length=None)
        )

    async def count(self, matcher: dict = {}) -> int:
        return await (await self.collection).count_documents(matcher)

    async def delete(self, id: Any = None, matcher: dict = {}) -> int:
        if id is not None:
            matcher.update({"id": id})
        if not matcher:
            return
        return (await (await self.collection).delete_one(matcher)).deleted_count

    async def deleteAll(self, matcher: dict) -> int:
        if not matcher:
            return
        return (await (await self.collection).delete_many(matcher)).deleted_count

    async def batch_delete(self, matcher: dict = {}) -> int:
        return (await (await self.collection).delete_many(matcher)).deleted_count

    async def sample(self, sample: int, matcher: dict = {}, projection: dict = {}, sort: List = []) -> List:
        projection.update({"_id": False})
        param = []
        if matcher:
            param.append({'$match': matcher})
        if sort:
            param.append({'$sort': dict(sort)})
        if projection:
            param.append({'$project': projection})
        param.append({'$sample': {'size': sample}})
        return await (await self.collection).aggregate(param).to_list(length=None)

    async def distinct(self, key: str, matcher: dict = {}, cached: dict = None) -> List:
        if cached:

            @cache(**cached)
            async def query(key: str, matcher: dict) -> List:
                return await (await self.collection).find(matcher).distinct(key)

            return await query(key, matcher)
        return await (await self.collection).find(matcher).distinct(key)

    async def index(self, param: List = [], page: int = 1, page_size: int = 20, sort={}, cached: dict = None) -> dict:
        if sort:
            param.append({'$sort': sort})
        param.append(
            {
                '$facet': {
                    'total': [{'$count': "count"}],
                    'records': [{'$project': {'_id': False}}, {'$skip': page_size * (page - 1)}, {'$limit': page_size}],
                }
            }
        )
        param.append(
            {
                '$project': {
                    'records': "$records",
                    'total': {'$ifNull': [{'$arrayElemAt': ["$total.count", 0]}, 0]},
                }
            }
        )
        return ((await self.query(param, cached=cached)) or [{'records': [], 'total': 0}]).pop(0)

    def default_query(self, matcher: dict) -> dict:
        return [{'$match': matcher}]

    async def count_query(self, param: List, cached: dict = None) -> int:
        param.append({'$group': {"_id": None, "count": {"$sum": 1}}})
        return (await self.query(param, cached=cached) or [{'count': 0}]).pop(0).get('count', 0)

    async def query(self, pipeline: List = [], sort={}, page: int = 1, page_size: int = 0, cached: dict = None) -> List:
        if sort:
            pipeline.append({'$sort': sort})
        if page > 1:
            pipeline.append({'$skip': page_size * (page - 1)})
        if page_size > 0:
            pipeline.append({'$limit': page_size})
        pipeline.append({'$project': {'_id': False}})
        if cached:

            @cache(**cached)
            async def use_cache(pipeline: List) -> List:
                return await (await self.collection).aggregate(pipeline).to_list(length=None)

            return await use_cache(pipeline)
        return await (await self.collection).aggregate(pipeline).to_list(length=None)
