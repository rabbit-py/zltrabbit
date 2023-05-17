# -*- coding: utf-8 -*-

from base.data_transform import protobuf_transformer
from base.util import date_utils
from base.di.service_location import service
from motor.motor_asyncio import AsyncIOMotorClient


class CommonDAHelper():

    @property
    def client(self) -> AsyncIOMotorClient:
        return service.get(self.name).get_client()

    @property
    def collection(self):
        return service.get(self.name).get_client()[self.db][self.coll]

    def __init__(self, db: str, coll: str, name: str = 'db.default') -> None:
        self.name = name
        self.db = db
        self.coll = coll
        self.id_generator = service.id_generator

    async def add_or_update(self, template, matcher: dict = None, keep_key: bool = False) -> dict:
        tmp = template
        if not isinstance(tmp, dict):
            tmp = protobuf_transformer.protobuf_to_dict(template, preserving_proto_field_name=keep_key)
        if not tmp.get('id'):
            tmp.update({'id': self.id_generator.generate_id()})
        if not tmp.get('create_time' if keep_key else 'createTime') or tmp.get('create_time' if keep_key else 'createTime') in [0, '0']:
            tmp.update({'create_time' if keep_key else 'createTime': date_utils.timestamp_second()})
        if matcher is None:
            matcher = {"id": tmp.get('id')}
        tmp.update({'update_time' if keep_key else 'updateTime': date_utils.timestamp_second()})
        try:
            async with await self.client.start_session(causal_consistency=True) as session:
                async with session.start_transaction():
                    await self.collection.update_one(matcher, {"$set": tmp}, upsert=True)
                    return tmp
        except Exception as e:
            raise e

    async def get(self, id: str = None, matcher: dict = {}, projection: dict = {}, sort: list = []) -> dict:
        if id is not None:
            matcher.update({"id": id})
        if not matcher:
            return
        projection.update({"_id": False})
        return await self.collection.find_one(matcher, projection=projection, sort=sort)

    async def list(self, matcher: dict = {}, projection: dict = {}, page: int = 1, page_size: int = 0, sort=[]) -> list:
        page = page if page > 0 else 1
        projection.update({"_id": False})
        return await self.collection.find(matcher, projection=projection,
                                          sort=sort).skip(page_size * (page - 1)).limit(page_size).to_list(length=None)

    async def delete(self, id: str = None, matcher: dict = {}) -> int:
        if id is not None:
            matcher.update({"id": id})
        if not matcher:
            return
        result = await self.collection.delete_one(matcher)
        return result.deleted_count

    async def sample(self, sample: int, matcher: dict = {}, projection: dict = {}, sort: list = []) -> list:
        projection.update({"_id": False})
        param = []
        if matcher:
            param.append({'$match': matcher})
        if sort:
            param.append({'$sort': sort})
        if sample:
            param.append({'$sample': {'size': sample}})
        param.append({'$project': projection})
        return await self.collection.aggregate(param).to_list(length=None)

    async def distinct(self, key: str, matcher: dict = {}) -> list:
        return await self.collection.find(matcher).distinct(key)
