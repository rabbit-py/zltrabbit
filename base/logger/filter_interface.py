# -*- coding: utf-8 -*-

from abc import abstractmethod, ABCMeta


class FilterInterface(metaclass=ABCMeta):

    @abstractmethod
    def filter(self, record: dict) -> bool:
        pass