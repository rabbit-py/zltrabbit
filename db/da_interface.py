# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from typing import List, Union

from db.base_model import BaseModel


class DaInterface(metaclass=ABCMeta):
    @abstractmethod
    async def save(self, model: Union[BaseModel, dict], matcher: dict = None, projection={}) -> dict:
        pass

    @abstractmethod
    async def batch_save(self, models: list[Union[BaseModel, dict]], matcher: list = None) -> int:
        pass

    @abstractmethod
    async def updateAll(self, data: dict, matcher: dict) -> int:
        pass

    @abstractmethod
    async def get(self, id: str = None, matcher: dict = {}, projection: dict = {}, sort: list = [], **kwargs) -> dict:
        pass

    @abstractmethod
    async def list(
        self, matcher: dict = {}, projection: dict = {}, page: int = 1, page_size: int = 0, sort=[], **kwargs
    ) -> List:
        pass

    @abstractmethod
    async def count(self, matcher: dict = {}) -> int:
        pass

    @abstractmethod
    async def delete(self, id: str = None, matcher: dict = {}) -> int:
        pass

    @abstractmethod
    async def deleteAll(self, matcher: dict = {}) -> int:
        pass

    @abstractmethod
    async def batch_delete(self, matcher: dict = {}) -> int:
        pass

    @abstractmethod
    async def index(self, param: List = [], page: int = 1, page_size: int = 20, sort={}, cached: dict = None) -> dict:
        pass

    @abstractmethod
    def default_query(self, matcher: dict) -> dict:
        pass

    @abstractmethod
    async def count_query(self, param: List, cached: dict = None) -> int:
        pass

    @abstractmethod
    async def query(self, pipeline: List = [], sort={}, page: int = 1, page_size: int = 0, cached: dict = None) -> List:
        pass

    @abstractmethod
    async def distinct(self, key: str, matcher: dict = {}, cached: dict = None) -> List:
        pass
