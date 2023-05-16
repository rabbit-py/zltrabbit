# -*- coding: utf-8 -*-

from contextvars import ContextVar
from typing import Any

COMMON_CONTEXT = 'context'

_common_ctx_var: ContextVar[dict] = ContextVar(COMMON_CONTEXT, default={})


def get(key: str, default: Any = None) -> Any:
    val = _common_ctx_var.get().get(key)
    if val is None:
        return default
    return val


def set(key: str, val: Any) -> None:
    _common_ctx_var.get().update({key: val})