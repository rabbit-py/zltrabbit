# -*- coding: utf-8 -*-

from typing import Any
from base.coroutine.context import context


class BaseContext:
    def __init__(self, key: str) -> None:
        self.key = key

    def get(self) -> Any:
        return context.get(self.key)

    def set(self, data: Any) -> None:
        context.set(self.key, data)

    def remove(self) -> None:
        context.remove(self.key)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.get(), name)
