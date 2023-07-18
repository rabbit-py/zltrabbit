# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from typing import Any


class CoderInterface(metaclass=ABCMeta):

    @abstractmethod
    def encode(self, content: Any) -> bytes:
        pass

    @abstractmethod
    def decode(cls, value: bytes) -> Any:
        pass