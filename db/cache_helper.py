from typing import Any
import ujson
from fastapi.encoders import jsonable_encoder
from fastapi_cache import Coder
from fastapi_cache import FastAPICache
from base.di.service_location import service
from base.functions import env


class UJsonCoder(Coder):

    @classmethod
    def encode(cls, value: Any) -> bytes:
        return ujson.dumps(
            value,
            default=jsonable_encoder,
        )

    @classmethod
    def decode(cls, value: bytes) -> Any:
        return ujson.loads(value)


def cache_setup(key: str = 'cache.default') -> None:
    FastAPICache.init(service.get(key), prefix=f"{env('APPNAME','Rabbit')}-cache", coder=UJsonCoder)
