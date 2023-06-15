# -*- coding: utf-8 -*-

from typing import Callable


class Pipeline:

    @property
    def data(self) -> list:
        return self._data

    def __init__(self) -> None:
        self._data = []

    def match(self, match: dict):
        if match:
            self._data.append({'$match': match})
        return self

    def lookup(self, lookup: dict):
        if lookup:
            self._data.append({'$lookup': lookup})
        return self

    def unwind(self, unwind: dict):
        if unwind:
            self._data.append({'$unwind': unwind})
        return self

    def project(self, project: dict):
        if project:
            self._data.append({'$project': project})
        return self

    def sort(self, sort: dict):
        if sort:
            self._data.append({'$sort': sort})
        return self

    def group(self, group: dict):
        if group:
            self._data.append({'$group': group})
        return self

    def facet(self, facet: dict):
        if facet:
            self._data.append({'$facet': facet})
        return self

    def limit(self, limit: int):
        if limit:
            self._data.append({'$limit': limit})
        return self

    def skip(self, skip: int):
        if skip:
            self._data.append({'$skip': skip})
        return self

    def replace_root(self, replace_root: dict):
        if replace_root:
            self._data.append({'$replaceRoot': replace_root})
        return self


class MatchHelper:
    match_map = {
        'like': lambda x: {
            '$regex': x
        },
        'not like': lambda x: {
            '$not': {
                '$regex': x
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

    def pipeline(self) -> Pipeline:
        return Pipeline()


match_helper = MatchHelper()
