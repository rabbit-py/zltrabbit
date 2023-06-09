# -*- coding: utf-8 -*-
import importlib
import inspect
from json import JSONDecodeError
import os
from fastapi import APIRouter, BackgroundTasks, FastAPI, HTTPException, Request, status
from fastapi.responses import UJSONResponse as _JSONResponse
from typing import Optional
from db.mongodb.common_da_helper import CommonDAHelper
from base.functions import to_lower_camel


class UJSONResponse(_JSONResponse):

    def __init__(
        self,
        content=None,
        code=0,
        msg: str = None,
        headers=None,
        status_code: int = 200,
        media_type="application/json; charset=utf-8",
        background: Optional[BackgroundTasks] = None,
    ):
        if not msg:
            msg = 'success'
        content = {"code": code, "msg": msg, "data": content}
        super(UJSONResponse, self).__init__(content, status_code, headers, media_type, background)


async def request_body(request: Request, exclude: list = [], with_matcher: bool = True) -> dict:
    try:
        body = {}
        if 'multipart/form-data' in request.headers.get('Content-Type', '') or 'application/x-www-form-urlencoded' in request.headers.get(
                'Content-Type', ''):
            body = dict(await request.form())
        elif await request.body():
            body = await request.json()
        if isinstance(body, dict):
            body = dict(dict(request.path_params, **request.query_params), **body)
            for key in exclude:
                key in body and body.pop(key)
        if with_matcher:
            return dict(body.pop('matcher'), **body) if 'matcher' in body else body
        return body
    except JSONDecodeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise e


def add_route(router: APIRouter,
              manager: CommonDAHelper,
              pb: object,
              keep_key: bool,
              before_events: dict = {},
              after_events: dict = {},
              exclude: list = []) -> None:

    if 'index' not in exclude:

        @router.post("")
        @router.get("")
        async def index(request: Request, page: Optional[int] = 1, pageSize: Optional[int] = 20) -> dict:
            matcher = await request_body(request)
            paged = matcher.pop('page{}', {})
            page = paged.pop('page', page)
            pageSize = paged.pop('pageSize', pageSize)
            if not keep_key:
                matcher = to_lower_camel(matcher)
            sort = matcher.pop('sort{}', None)
            if 'list' in before_events:
                param = await before_events['list'](matcher)
            else:
                param = [{'$match': matcher}]
            sort and param.append({'$sort': sort})
            param.append({
                '$facet': {
                    'total': [{
                        '$count': "count"
                    }],
                    'records': [{
                        '$project': {
                            '_id': False
                        }
                    }, {
                        '$skip': pageSize * (page - 1)
                    }, {
                        '$limit': pageSize
                    }]
                }
            })
            param.append({'$project': {
                'records': "$records",
                'total': {
                    '$ifNull': [{
                        '$arrayElemAt': ["$total.count", 0]
                    }, 0]
                },
            }})
            result = ((await manager.aggregate(param)) or [{'records': [], 'total': 0}]).pop(0)
            if 'list' in after_events:
                await after_events['list'](param, result['records'])
            return result

    if 'list' not in exclude:

        @router.post("/list")
        @router.get("/list")
        async def all(request: Request, page: Optional[int] = 1, pageSize: Optional[int] = 0) -> list:
            matcher = await request_body(request)
            paged = matcher.pop('page{}', {})
            page = paged.pop('page', page)
            pageSize = paged.pop('pageSize', pageSize)
            if not keep_key:
                matcher = to_lower_camel(matcher)
            sort = matcher.pop('sort{}', None)
            if 'list' in before_events:
                param = await before_events['list'](matcher)
            else:
                param = [{'$match': matcher}, {'$project': {'_id': False}}]
            sort and param.append({'$sort': sort})
            result = (await manager.aggregate(param, page=page, page_size=pageSize)) or []
            if 'list' in after_events:
                await after_events['list'](param, result)
            return result

    if 'get' not in exclude:

        @router.post("/get")
        @router.get("/get")
        @router.get("/get/{id}")
        async def get(request: Request, id: str = None) -> dict:
            matcher = await request_body(request)
            if id is None and not matcher and not before_events:
                return {}
            if not keep_key:
                matcher = to_lower_camel(matcher)
            sort = matcher.pop('sort{}', None)
            if 'get' in before_events:
                param = await before_events['get'](matcher)
            else:
                param = [{'$match': matcher if not id else dict(matcher, **{'id': id})}]
            sort and param.append({'$sort': sort})
            result = ((await manager.aggregate(param)) or [{}]).pop(0)
            if 'get' in after_events:
                await after_events['get'](param, result)
            return result

    if 'save' not in exclude:

        @router.post("/update")
        @router.post("/create")
        @router.post("/save")
        async def update(request: Request) -> dict:
            param = await request_body(request, with_matcher=False)
            if not param:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='参数不能为空')
            if not keep_key:
                param = to_lower_camel(param)
            result = await manager.add_or_update(**(await before_events['save'](param) if 'save' in before_events else {
                'data': param
            }),
                                                 keep_key=keep_key,
                                                 pb=pb)
            if 'save' in after_events:
                await after_events['save'](param, result)
            return result

        @router.post("/batch_update")
        @router.post("/batch_create")
        @router.post("/batch_save")
        async def batch_update(request: Request) -> bool:
            param = await request_body(request, with_matcher=False)
            if not param:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='参数不能为空')

            if not keep_key:
                for item in param:
                    item = to_lower_camel(item)
            result = await manager.batch_add_or_update(**(await before_events['batch'](param) if 'batch' in before_events else {
                'datas': param
            }),
                                                       keep_key=keep_key,
                                                       pb=pb)
            if 'batch' in after_events:
                await after_events['batch'](item, result)
            return True

    if 'delete' not in exclude:

        @router.delete("/{id}")
        @router.post("/delete/{id}")
        async def delete(id: str) -> int:
            return (await manager.delete(id)).deleted_count

    if 'distinct' not in exclude:

        @router.get("/distinct")
        @router.post("/distinct")
        async def distinct(request: Request, key: str) -> list:
            matcher = await request_body(request, ['key'])
            if not keep_key:
                matcher = to_lower_camel(matcher)
            if 'distinct' in before_events:
                param = await before_events['distinct'](matcher)
            else:
                param = {'matcher': matcher}
            result = await manager.distinct(key, **param)
            if 'distinct' in after_events:
                await after_events['distinct'](param, result)
            return result


class BaseRouter:

    @property
    def router(self):
        return self._router

    def __init__(self,
                 router: APIRouter,
                 manager: CommonDAHelper,
                 pb: object = None,
                 keep_key: bool = False,
                 before_events: dict = {},
                 after_events: dict = {},
                 exclude: list = ['delete']) -> None:
        self._router = router
        self._router.default_response_class = UJSONResponse
        add_route(router, manager, pb, keep_key, before_events, after_events, exclude)


def auto_import(path: str, app: FastAPI) -> None:
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.isdir(file_path):
            auto_import(file_path, app)
        elif file != '__init__.py' and file.endswith('.py'):
            file_mode = '%s.%s' % (path.replace('\\', '.').replace('/', '.'), os.path.splitext(file)[0])
            mode_obj = importlib.import_module(file_mode)
            classes = inspect.getmembers(mode_obj, inspect.isclass)
            for name, cls in classes:
                if hasattr(cls, 'router') and name != 'BaseRouter':
                    router = cls().router
                    if isinstance(router, APIRouter):
                        app.include_router(cls().router)
