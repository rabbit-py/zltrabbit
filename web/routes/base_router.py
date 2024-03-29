# -*- coding: utf-8 -*-
import importlib
import inspect
from json import JSONDecodeError
import os, xmltodict
from fastapi import APIRouter, BackgroundTasks, FastAPI, HTTPException, Request, status
from fastapi.responses import ORJSONResponse as _JSONResponse
from typing import Optional
from db.base_model import BaseModel
from db.da_interface import DaInterface
from base.functions import to_lower_camel


class JSONResponse(_JSONResponse):
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
        super(JSONResponse, self).__init__(content, status_code, headers, media_type, background)


async def request_body(request: Request, exclude: list = [], with_matcher: bool = True) -> dict:
    try:
        body = {}
        if 'multipart/form-data' in request.headers.get(
            'Content-Type', ''
        ) or 'application/x-www-form-urlencoded' in request.headers.get('Content-Type', ''):
            body = dict(await request.form())
        elif 'application/xml' in request.headers.get('Content-Type', ''):
            body = await request.body()
            body = xmltodict.parse(body).get('xml')
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


def add_route(
    router: APIRouter,
    manager: DaInterface,
    model: BaseModel,
    before_events: dict = {},
    after_events: dict = {},
    cached: dict = {},
    exclude: list = [],
) -> None:
    if 'index' not in exclude:

        @router.post("")
        @router.get("")
        async def index(request: Request, page: Optional[int] = 1, pageSize: Optional[int] = 20) -> dict:
            matcher = await request_body(request)
            query = matcher.pop('query{}', {})
            matcher = dict(matcher, **query)
            paged = matcher.pop('page{}', {})
            page = int(paged.pop('page', matcher.pop('page', page)))
            pageSize = int(paged.pop('pageSize', matcher.pop('pageSize', pageSize)))
            if model.key_style == BaseModel.STYLE_LOWER_CAMEL:
                matcher = to_lower_camel(matcher)
            sort = matcher.pop('sort{}', None)
            if 'index' in before_events:
                param = (
                    (await before_events['index'](matcher))
                    if inspect.iscoroutinefunction(before_events['index'])
                    else before_events['index'](matcher)
                )
            else:
                param = manager.default_query(matcher)
            if not param:
                return []
            result = await manager.index(param, page=page, page_size=pageSize, sort=sort, cached=cached.get('index'))
            if 'index' in after_events:
                result['records'] = (
                    await after_events['index'](matcher, result['records'])
                    if inspect.iscoroutinefunction(after_events['index'])
                    else after_events['index'](matcher, result['records'])
                )
            return result

    if 'list' not in exclude:

        @router.post("/list")
        @router.get("/list")
        async def all(request: Request, page: Optional[int] = 1, pageSize: Optional[int] = 0) -> list:
            matcher = await request_body(request)
            query = matcher.pop('query{}', {})
            matcher = dict(matcher, **query)
            paged = matcher.pop('page{}', {})
            page = int(paged.pop('page', matcher.pop('page', page)))
            pageSize = int(paged.pop('pageSize', matcher.pop('pageSize', pageSize)))
            if model.key_style == BaseModel.STYLE_LOWER_CAMEL:
                matcher = to_lower_camel(matcher)
            sort = matcher.pop('sort{}', None)
            if 'list' in before_events:
                param = (
                    await before_events['list'](matcher)
                    if inspect.iscoroutinefunction(before_events['list'])
                    else before_events['list'](matcher)
                )
            else:
                param = manager.default_query(matcher)
            if not param:
                return []
            result = (await manager.query(param, sort=sort, page=page, page_size=pageSize, cached=cached.get('list'))) or []
            if 'list' in after_events:
                result = (
                    await after_events['list'](matcher, result)
                    if inspect.iscoroutinefunction(after_events['list'])
                    else after_events['list'](matcher, result)
                )

            return result

    if 'get' not in exclude:

        @router.post("/get")
        @router.get("/get")
        @router.get("/get/{id}")
        async def get(request: Request, id: str = None) -> dict:
            matcher = await request_body(request)
            query = matcher.pop('query{}', {})
            matcher = dict(matcher, **query)
            if id is None and not matcher and not before_events:
                return {}
            if model.key_style == BaseModel.STYLE_LOWER_CAMEL:
                matcher = to_lower_camel(matcher)
            sort = matcher.pop('sort{}', None)
            if 'get' in before_events:
                param = (
                    await before_events['get'](matcher)
                    if inspect.iscoroutinefunction(before_events['get'])
                    else before_events['get'](matcher)
                )
            else:
                param = manager.default_query(matcher if not id else dict(matcher, **{'id': id}))
            if not param:
                return {}
            result = ((await manager.query(param, sort=sort, cached=cached.get('get'))) or [{}]).pop(0)
            if 'get' in after_events:
                result = (
                    await after_events['get'](matcher, result)
                    if inspect.iscoroutinefunction(after_events['get'])
                    else after_events['get'](matcher, result)
                )
            return result

    if 'save' not in exclude:

        @router.post("/update")
        @router.post("/create")
        @router.post("/save")
        async def update(request: Request) -> dict:
            param = await request_body(request, with_matcher=False)
            param = model.copy().load(param)
            if 'save' in before_events:
                param = (
                    await before_events['save'](param)
                    if inspect.iscoroutinefunction(before_events['save'])
                    else before_events['save'](param)
                )
            else:
                param = {'model': param}
            if not param or not param.get('model'):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='参数不能为空')
            result = await manager.save(**param)
            if 'save' in after_events:
                result = (
                    await after_events['save'](param, result)
                    if inspect.iscoroutinefunction(after_events['save'])
                    else after_events['save'](param, result)
                )
            return result

        @router.post("/batch_update")
        @router.post("/batch_create")
        @router.post("/batch_save")
        async def batch_update(request: Request) -> bool:
            param = await request_body(request, with_matcher=False)
            for i, item in enumerate(param):
                param[i] = model.copy().load(item)
            if 'batch' in before_events:
                param = (
                    await before_events['batch'](param)
                    if inspect.iscoroutinefunction(before_events['batch'])
                    else before_events['batch'](param)
                )
            else:
                param = {'models': param}
            if not param or not param.get('models'):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='参数不能为空')
            result = await manager.batch_save(**param)
            if 'batch' in after_events:
                result = (
                    await after_events['batch'](item, result)
                    if inspect.iscoroutinefunction(after_events['batch'])
                    else after_events['batch'](item, result)
                )
            return True

    if 'count' not in exclude:

        @router.get("/count")
        @router.post("/count")
        async def count(request: Request) -> int:
            matcher = await request_body(request)
            query = matcher.pop('query{}', {})
            matcher = dict(matcher, **query)
            if model.key_style == BaseModel.STYLE_LOWER_CAMEL:
                matcher = to_lower_camel(matcher)
            if 'count' in before_events:
                param = (
                    await before_events['count'](matcher)
                    if inspect.iscoroutinefunction(before_events['count'])
                    else before_events['count'](matcher)
                )
            else:
                param = manager.default_query(matcher)
            result = await manager.count_query(param, cached=cached.get('distinct'))
            if 'count' in after_events:
                result = (
                    await after_events['count'](param, result)
                    if inspect.iscoroutinefunction(after_events['count'])
                    else after_events['count'](param, result)
                )
            return result

    if 'delete' not in exclude:

        @router.delete("/{id}")
        @router.post("/delete/{id}")
        async def delete(id: str) -> int:
            ret = True
            if 'delete' in before_events:
                ret = (
                    await before_events['delete'](id)
                    if inspect.iscoroutinefunction(before_events['delete'])
                    else before_events['delete'](id)
                )
            result = (await manager.delete(id)) if ret else 0
            if 'delete' in after_events:
                result = (
                    await after_events['delete'](id, result)
                    if inspect.iscoroutinefunction(after_events['delete'])
                    else after_events['delete'](id, result)
                )
            return result

    if 'distinct' not in exclude:

        @router.get("/distinct")
        @router.post("/distinct")
        async def distinct(request: Request, key: str) -> list:
            matcher = await request_body(request, ['key'])
            if model.key_style == BaseModel.STYLE_LOWER_CAMEL:
                matcher = to_lower_camel(matcher)
            if 'distinct' in before_events:
                param = (
                    await before_events['distinct'](key, matcher)
                    if inspect.iscoroutinefunction(before_events['distinct'])
                    else before_events['distinct'](key, matcher)
                )
            else:
                param = matcher
            result = await manager.distinct(key, param, cached=cached.get('distinct'))
            if 'distinct' in after_events:
                result = (
                    await after_events['distinct'](key, param, result)
                    if inspect.iscoroutinefunction(after_events['distinct'])
                    else after_events['distinct'](key, param, result)
                )
            return result


class BaseRouter:
    @property
    def router(self):
        return self._router

    def __init__(
        self,
        router: APIRouter,
        manager: DaInterface,
        model: BaseModel = BaseModel(),
        before_events: dict = {},
        after_events: dict = {},
        cached: dict = {},
        exclude: list = ['delete'],
    ) -> None:
        self._router = router
        self._router.default_response_class = JSONResponse
        add_route(router, manager, model, before_events, after_events, cached, exclude)


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
