# -*- coding: utf-8 -*-

from abc import abstractmethod, ABCMeta


class StorageInterface(metaclass=ABCMeta):

    @abstractmethod
    def save_token(self, token: dict, key: str = 'id', expired: int = 7200) -> None:
        ...

    @abstractmethod
    def check_token(self, token: str, key: str = 'id') -> bool:
        ...

    @abstractmethod
    def del_token(self, token: str, key: str = 'id') -> None:
        ...