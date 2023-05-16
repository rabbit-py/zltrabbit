# -*- coding: utf-8 -*-

import abc
import random

from sms.code.storage_interface import StorageInterface


class SmsInterface(metaclass=abc.ABCMeta):

    def __init__(self, name: str, storage: StorageInterface, config: dict) -> None:
        self._name = name
        self._storage = storage
        self._config = config

    @abc.abstractmethod
    async def send_code(self, phoneNumbers: list, use_template: str) -> bool:
        pass

    @abc.abstractmethod
    async def send_sms(self, phoneNumbers: list, template_code: str, template_param: dict = {}) -> bool:
        pass

    def generate_code(self) -> str:
        return str(random.randint(100000, 999999))

    async def save_code(self, username: str, code: str, expire: int = 300) -> bool:
        return await self._storage.save(self._name, username, code, expire)

    async def get_code(self, username: str) -> str:
        return await self._storage.get(self._name, username)