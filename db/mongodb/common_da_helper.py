# -*- coding: utf-8 -*-

from typing import List, Tuple

from pymongo import ReturnDocument, UpdateOne
from pymongo.results import BulkWriteResult, DeleteResult
from base.data_transform import protobuf_transformer
from base.util import date_utils
from base.di.service_location import service
from base.coroutine.context import context
from motor.motor_asyncio import AsyncIOMotorClientSession, AsyncIOMotorCollection


class CommonDAHelper():

    @property
    def session(self) -> AsyncIOMotorClientSession:
        return context.get('mongo_session')

    @property
    def collection(self) -> AsyncIOMotorCollection:
        return service.get(self.name).get_client()[self.db][self.coll]

    def __init__(self, db: str, coll: str, name: str = 'db.default') -> None:
        self.name = name
        self.db = db
        self.coll = coll
        self.id_generator = service.id_generator

    def prefix_data(self, data: dict, keep_key: bool = False, pb: object = None) -> Tuple:
        pb_tmp = {'id': data.pop('id', None)}
        if pb is not None:
            pb_tmp = dict(
                protobuf_transformer.protobuf_to_dict(protobuf_transformer.dict_to_protobuf(data, pb), preserving_proto_field_name=keep_key),
                **pb_tmp)
            for key in [x for x in data.keys()]:
                if key not in pb_tmp:
                    data.pop(key)
        if not pb_tmp.get('id'):
            pb_tmp.update({'id': self.id_generator.generate_id()})
        time = date_utils.timestamp_second()
        create_time_key = 'create_time' if keep_key else 'createTime'
        if not pb_tmp.get(create_time_key) or pb_tmp.get(create_time_key) in [0, '0']:
            pb_tmp.update({create_time_key: time})
        elif create_time_key in pb_tmp:
            pb_tmp.update({create_time_key: int(pb_tmp[create_time_key])})
        data.update({'update_time' if keep_key else 'updateTime': time})
        return data, pb_tmp

    async def add_or_update(self, data: dict, matcher: dict = None, projection={}, keep_key: bool = False, pb: object = None) -> dict:
        data, pb_tmp = self.prefix_data(data, keep_key, pb)
        if matcher is None:
            matcher = {"id": pb_tmp.get('id')}
        projection.update({"_id": False})
        return await self.collection.find_one_and_update(matcher, {
            "$set": data,
            '$setOnInsert': dict(filter(lambda x: x[0] not in data, pb_tmp.items()))
        },
                                                         return_document=ReturnDocument.AFTER,
                                                         upsert=True,
                                                         projection=projection,
                                                         session=self.session)

    async def batch_add_or_update(self, datas: list, matcher: list = None, keep_key: bool = False, pb: object = None) -> BulkWriteResult:
        bulk_write_data = []
        for data in datas:
            data, pb_tmp = self.prefix_data(data, keep_key, pb)
            if matcher is None:
                condition = {"id": pb_tmp.get('id')}
            else:
                condition = {}
                for key in matcher:
                    condition.update({key: data.get(key)})
            bulk_write_data.append(
                UpdateOne(condition, {
                    "$set": data,
                    '$setOnInsert': dict(filter(lambda x: x[0] not in data, pb_tmp.items()))
                }, upsert=True))

        return await self.collection.bulk_write(bulk_write_data, session=self.session)

    async def get(self, id: str = None, matcher: dict = {}, projection: dict = {}, sort: list = [], **kwargs) -> dict:
        if id is not None:
            matcher.update({"id": id})
        if not matcher:
            return
        projection.update({"_id": False})
        return (await self.collection.find_one(matcher, projection=projection, sort=sort, **kwargs)) or {}

    async def list(self, matcher: dict = {}, projection: dict = {}, page: int = 1, page_size: int = 0, sort=[], **kwargs) -> List:
        page = page if page > 0 else 1
        projection.update({"_id": False})
        return await self.collection.find(matcher, projection=projection, sort=sort,
                                          **kwargs).skip(page_size * (page - 1)).limit(page_size).to_list(length=None)

    async def count(self, matcher: dict = {}) -> int:
        return await self.collection.count_documents(matcher)

    async def delete(self, id: str = None, matcher: dict = {}) -> DeleteResult:
        if id is not None:
            matcher.update({"id": id})
        if not matcher:
            return
        return await self.collection.delete_one(matcher)

    async def batch_delete(self, matcher: dict = {}) -> DeleteResult:
        return await self.collection.delete_many(matcher)

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
        return await self.collection.aggregate(param).to_list(length=None)

    async def distinct(self, key: str, matcher: dict = {}) -> List:
        return await self.collection.find(matcher).distinct(key)

    async def aggregate(self, pipeline: List = [], page: int = 1, page_size: int = 0) -> List:
        if page > 1:
            pipeline.append({'$skip': page_size * (page - 1)})
        if page_size > 0:
            pipeline.append({'$limit': page_size})
        pipeline.append({'$project': {'_id': False}})
        return await self.collection.aggregate(pipeline).to_list(length=None)
