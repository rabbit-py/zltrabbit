# -*- coding: utf-8 -*-
from typing import Any
from .coder_interface import CoderInterface
try:
    import ujson
except ImportError:  # pragma: nocover
    ujson = None  # type: ignore

try:
    import orjson
except ImportError:  # pragma: nocover
    orjson = None  # type: ignore


class UJSONCoder(CoderInterface):

    @classmethod
    def encode(self, content: Any) -> bytes:
        assert ujson is not None, "ujson must be installed to use UJSONCoder"
        return ujson.dumps(content, ensure_ascii=False).encode("utf-8")

    @classmethod
    def decode(cls, value: bytes) -> Any:
        return ujson.loads(value)


class ORJSONCoder(CoderInterface):

    @classmethod
    def encode(self, content: Any) -> bytes:
        assert orjson is not None, "orjson must be installed to use ORJSONCoder"
        return orjson.dumps(content, option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY)

    @classmethod
    def decode(cls, value: bytes) -> Any:
        return orjson.loads(value)
