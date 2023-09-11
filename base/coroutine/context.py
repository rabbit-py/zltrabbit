# -*- coding: utf-8 -*-

from contextvars import ContextVar
from typing import Any


class Context:
    def __init__(self, name='context') -> None:
        self._common_ctx_var: ContextVar[dict] = ContextVar(name, default={})

    def get(self, key: str, default: Any = None) -> Any:
        val = self._common_ctx_var.get().get(key)
        if val is None:
            return default
        return val

    def set(self, key: str, val: Any) -> None:
        self._common_ctx_var.get().update({key: val})

    def clear(self) -> None:
        self._common_ctx_var.set({})

    def remove(self, key: str) -> None:
        data = self._common_ctx_var.get()
        data.pop(key, None)


context = Context()
