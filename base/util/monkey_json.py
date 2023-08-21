# -*- coding: utf-8 -*-

import datetime
from ipaddress import IPv4Address
import json
from typing import Any
try:
    import ujson
except ImportError:  # pragma: nocover
    ujson = None  # type: ignore

try:
    import orjson
except ImportError:  # pragma: nocover
    orjson = None  # type: ignore


class UJSONEncoder(json.JSONEncoder):
    
    def default(self, o: Any) -> Any:
        try:
            if isinstance(o, datetime.datetime):
                return o.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(o, datetime.date):
                return o.strftime('%Y-%m-%d')
            elif isinstance(o, IPv4Address):
                return str(o)
            return ujson.dumps(o,
                               skipkeys=self.skipkeys,
                               ensure_ascii=self.ensure_ascii,
                               allow_nan=self.allow_nan,
                               indent=self.indent,
                               sort_keys=self.sort_keys,
                               default=self.default)
        except TypeError:
            return json.JSONEncoder.default(self, o)

    def encode(self, o: Any) -> str:
        assert ujson is not None, "ujson must be installed to use UJSONCoder"
        try:
            return self.default(o)
        except TypeError:
            return super().encode(o)


class ORJSONEncoder(json.JSONEncoder):

    def default(self, o: Any) -> Any:
        try:
            if isinstance(o, datetime.datetime):
                return o.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(o, datetime.date):
                return o.strftime('%Y-%m-%d')
            elif isinstance(o, IPv4Address):
                return str(0)
            option = orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY
            if self.indent:
                option |= orjson.OPT_INDENT_2
            if self.sort_keys:
                option |= orjson.OPT_SORT_KEYS
            return orjson.dumps(o, option=option).decode()
        except TypeError:
            return json.JSONEncoder.default(self, o)

    def encode(self, o: Any) -> str:
        try:
            return self.default(o)
        except TypeError:
            return super().encode(o)


def monkey_patch_json(name: str = 'orjson') -> None:
    json.__name__ = name
    if name == 'orjson':
        assert orjson is not None, "orjson must be installed to use ORJSONCoder"
        json._default_encoder = ORJSONEncoder(skipkeys=False,
                                              ensure_ascii=False,
                                              check_circular=True,
                                              allow_nan=True,
                                              indent=None,
                                              sort_keys=False,
                                              separators=None,
                                              default=None)
    else:
        assert ujson is not None, "ujson must be installed to use UJSONCoder"
        json._default_encoder = UJSONEncoder(
            skipkeys=False,
            ensure_ascii=False,
            check_circular=True,
            allow_nan=True,
            indent=None,
            sort_keys=False,
            separators=None,
            default=None,
        )
