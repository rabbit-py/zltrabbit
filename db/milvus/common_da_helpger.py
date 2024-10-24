# -*- encoding: utf-8 -*-
import asyncio
import functools
from typing import Any, Callable, List, Dict, Optional
from base.di.service_location import service
from loguru import logger
from pymilvus import CollectionSchema, utility, Collection, exceptions
from base.types import P


class CommonDAHelper(object):
    def __init__(
        self,
        db: str,
        coll: str,
        name: str = "default",
        loop: asyncio.AbstractEventLoopPolicy = None,
    ):
        self.name = name
        self.db = db
        self.coll = coll
        self._collection_map: Dict[str, Collection] = dict()
        self._lock = asyncio.Lock()
        self._conn = service.get(self.name)
        if not loop:
            loop = asyncio.get_running_loop()
        self._loop = loop

    @property
    def collection(self) -> Collection:
        collection = self._collection_map.get(self.coll)
        if not collection:
            self._collection_map[self.coll] = self._conn.get_client()
        return self._collection_map[self.coll]

    async def get_tb_info(self) -> dict:
        if await self.exists_tb(self.coll):
            collection = self.collection
            return {
                "base_info": str(collection).split("\n")[2:-1],
                "count": collection.num_entities,
            }
        return {}

    async def exists_tb(self, tb_name: str) -> bool:
        try:
            return await self.async_run(utility.has_collection, tb_name, using=self.collection._using)
        except exceptions.SchemaNotReadyException:
            return False
        except Exception as e:
            logger.error(e)
            raise e

    async def exists_index(self, collection: Collection) -> bool:
        return await self.async_run(collection.has_index)

    async def rename_tb(self, old_name: str, new_name: str) -> Any:
        if await self.exists_tb(old_name):
            return await self.async_run(
                utility.rename_collection,
                old_name,
                new_name,
                using=self.collection._using,
            )

    async def list_tbs(self) -> list:
        return await self.async_run(utility.list_collections, using=self.collection._using)

    async def drop_tb(self, tb_name: str = None):
        tb_name = tb_name or self.coll
        if await self.exists_tb(tb_name):
            self.collection.drop()

    async def create_index_tb(self, schema: Optional[CollectionSchema]) -> Collection:
        async with self._lock:
            client = self._conn.get_client()
            collection = client(name=self.coll, schema=schema, using=self._conn.alias)
            if not (await self.exists_index(collection)):
                index_params = {
                    "metric_type": "IP",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 1000},  # 聚类个数，过大或过小损失搜索精度
                }
                await self.async_run(
                    collection.create_index,
                    field_name="embedding",
                    index_params=index_params,
                )
            await self.async_run(collection.load, _async=True)
            self._collection_map[self.coll] = collection
            return collection

    def _batch_data(self, data: list, batch_size=100) -> list:
        result = [[field[i : i + batch_size] for i in range(0, len(field), batch_size)] for field in data]
        return result

    async def bulk_insert(self, data: List[list], schema: Optional[CollectionSchema], bulk_size: int = 100) -> int:
        if not await self.exists_tb(self.coll):
            await self.create_index_tb(schema)
        collection = self.collection
        result = self._batch_data(data, bulk_size)
        for batch in zip(*result):
            try:
                await self.async_run(collection.insert, list(batch))
            except exceptions.MilvusException as e:
                logger.error(f"insert data error, error_msg={e}")
                continue
        await self.async_run(collection.flush)
        return collection.num_entities

    async def query(self, expr: str, *args, **kwargs) -> list:
        if not (await self.exists_tb(self.coll)):
            raise Exception(f"Collection {self.coll} not exists!")
        return await self.async_run(self.collection.query, *args, expr=expr, **kwargs)

    async def delete(self, query_expr: str = None, ids: list = [], id_name: str = "id") -> int:
        if not (await self.exists_tb(self.coll)):
            return
        if query_expr is not None:
            ids = await self.async_run(self.collection.query, query_expr)
            if not ids:
                return
            id_name = list(ids[0].keys())[0]
            ids = map(lambda x: str(x["id"]), ids)
        ids = ",".join(map(str, ids))
        ret = await self.async_run(self.collection.delete, f"{id_name} in [{ids}]")
        await self.async_run(self.collection.flush)
        return ret.delete_count

    async def search(
        self,
        query_embeddings: str,
        search_params: dict,
        output_fields: list,
        expr: str = None,
        offset: int = 0,
        limit: int = 100,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> list:
        search_params["offset"] = offset
        hits = await self.async_run(
            self.collection.search,
            query_embeddings,
            anns_field="embedding",
            param=search_params,
            expr=(expr or None),
            output_fields=output_fields,
            limit=limit,
            **kwargs,
        )
        if not hits:
            return []

        result = []
        for h in hits:
            tmp = [{"score": round(row.distance, 4), **row.fields} for row in h]
            result.append(tmp)
        return result

    async def async_run(self, func: Callable, *args: P.args, **kwargs: P.kwargs) -> Any:
        return await self._loop.run_in_executor(None, functools.partial(func, *args, **kwargs))
