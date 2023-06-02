# -*- coding: utf-8 -*-

from typing import Callable


class MatchHelper:
    match_map = {
        'like': lambda x: {
            '$regex': x,
            '$options': '-i'
        },
        'not like': lambda x: {
            '$not': {
                '$regex': x,
                '$options': '-i'
            }
        },
        'in': lambda x: {
            '$in': x
        },
        'between': lambda x: filter(lambda y: x[1] is not None, {
            '$gte': x.pop(0, None),
            '$lte': x.pop(0, None)
        }.items()),
        '>': lambda x: {
            '$gt': x
        },
        '<': lambda x: {
            '$lt': x
        },
        '>=': lambda x: {
            '$gte': x
        },
        '<=': lambda x: {
            '$lte': x
        },
        '!=': lambda x: {
            '$not': x
        }
    }

    def convert(self, matcher: dict, convert_map: dict) -> None:
        for key in [x for x in matcher.keys()]:
            func = convert_map.get(key, matcher[key])
            matcher.update({key: func(matcher[key]) if isinstance(func, Callable) else func})


match_helper = MatchHelper()
