# -*- coding: utf-8 -*-

from typing import List, Tuple

from pymongo import ReturnDocument, UpdateOne
from pymongo.results import BulkWriteResult, DeleteResult
from base.data_transform import protobuf_transformer
from base.util import date_utils
from base.di.service_location import service
from base.coroutine.context import context
from motor.motor_asyncio import AsyncIOMotorClientSession, AsyncIOMotorCollection

from db.da_interface import DaInterface


class CommonDAHelper(DaInterface):

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
        create_time_key = 'create_time' if keep_key else 'createTime'
        data.pop(create_time_key, None)
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
        pb_tmp.update({create_time_key: time})
        data.update({'update_time' if keep_key else 'updateTime': time})
        return data, pb_tmp

    async def save(self, data: dict, matcher: dict = None, projection={}, keep_key: bool = False, pb: object = None) -> dict:
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

    async def batch_save(self, datas: list, matcher: list = None, keep_key: bool = False, pb: object = None) -> int:
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

        result = await self.collection.bulk_write(bulk_write_data, session=self.session)
        return result.inserted_count + result.modified_count

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

    async def delete(self, id: str = None, matcher: dict = {}) -> int:
        if id is not None:
            matcher.update({"id": id})
        if not matcher:
            return
        return (await self.collection.delete_one(matcher)).deleted_count

    async def batch_delete(self, matcher: dict = {}) -> int:
        return (await self.collection.delete_many(matcher)).deleted_count

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

    async def index(self, param: List = [], page: int = 1, page_size: int = 20, sort={}) -> dict:
        if sort:
            param.append({'$sort': sort})
        param.append({
            '$facet': {
                'total': [{
                    '$count': "count"
                }],
                'records': [{
                    '$project': {
                        '_id': False
                    }
                }, {
                    '$skip': page_size * (page - 1)
                }, {
                    '$limit': page_size
                }]
            }
        })
        param.append({'$project': {
            'records': "$records",
            'total': {
                '$ifNull': [{
                    '$arrayElemAt': ["$total.count", 0]
                }, 0]
            },
        }})
        return ((await self.query(param)) or [{'records': [], 'total': 0}]).pop(0)

    def default_query(self, matcher: dict) -> dict:
        return [{'$match': matcher}]

    async def count_query(self, param: List) -> int:
        param.append({'$group': {"_id": None, "count": {"$sum": 1}}})
        return (await self.query(param) or [{'count': 0}]).pop(0).get('count', 0)

    async def query(self, pipeline: List = [], sort={}, page: int = 1, page_size: int = 0) -> List:
        if sort:
            pipeline.append({'$sort': sort})
        if page > 1:
            pipeline.append({'$skip': page_size * (page - 1)})
        if page_size > 0:
            pipeline.append({'$limit': page_size})
        pipeline.append({'$project': {'_id': False}})
        return await self.collection.aggregate(pipeline).to_list(length=None)