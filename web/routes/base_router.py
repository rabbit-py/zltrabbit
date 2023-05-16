# -*- coding: utf-8 -*-
import importlib
import inspect
from json import JSONDecodeError
import os
from fastapi import APIRouter, BackgroundTasks, FastAPI, HTTPException, Request, params, status
from base.data_transform import protobuf_transformer
from fastapi.responses import UJSONResponse as _JSONResponse
from typing import Any, Dict, Optional, Callable
from db.mongodb.common_da_helper import CommonDAHelper
from pydantic.fields import Undefined


def Param(  # noqa: N802
    default: Any = Undefined,
    *,
    alias: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    gt: Optional[float] = None,
    ge: Optional[float] = None,
    lt: Optional[float] = None,
    le: Optional[float] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    regex: Optional[str] = None,
    example: Any = Undefined,
    examples: Optional[Dict[str, Any]] = None,
    **extra: Any,
) -> Any:
    return params.Param(
        default=default,
        alias=alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        regex=regex,
        example=example,
        examples=examples,
        **extra,
    )


class UJSONResponse(_JSONResponse):

    def __init__(
        self,
        content=None,
        code=200,
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
        if 'application/json' in request.headers.get('Content-Type') and await request.body():
            body = await request.json()
        elif 'multipart/form-data' in request.headers.get('Content-Type') or 'application/x-www-form-urlencoded' in request.headers.get(
                'Content-Type'):
            body = dict(await request.form())

        body = dict(body, **request.path_params, **request.query_params)
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
              default_matcher: Callable = None,
              exclude: list = []) -> None:

    if 'index' not in exclude:

        @router.post("")
        @router.get("")
        async def index(request: Request, page: int = 1, page_size: int = 20) -> list:
            matcher = await request_body(request, ['page', 'page_size'])
            if default_matcher is not None:
                param = await default_matcher(matcher)
            else:
                param = {'matcher': matcher}
            return (await manager.list(page=page, page_size=page_size, **param)) or []

    if 'list' not in exclude:

        @router.post("/list")
        @router.get("/list")
        async def all(request: Request, page: int = 1, page_sze: int = 0) -> list:
            matcher = await request_body(request, ['page', 'page_size'])
            if default_matcher is not None:
                param = await default_matcher(matcher)
            else:
                param = {'matcher': matcher}
            return (await manager.list(page=page, page_size=page_sze, **param)) or []

    if 'get' not in exclude:

        @router.post("/get")
        @router.get("/get")
        @router.get("/get/{id}")
        async def get(request: Request, id: str = None) -> dict:
            matcher = await request_body(request, ['id'])
            if id is None and not matcher and default_matcher is None:
                return {}
            if default_matcher is not None:
                param = await default_matcher(matcher)
            else:
                param = {'matcher': matcher}
            return (await manager.get(id, **param)) or {}

    if 'create' not in exclude:

        @router.post("/create")
        async def create(request: Request) -> dict:
            param = await request_body(request, False)
            template = protobuf_transformer.dict_to_protobuf(param, pb) if pb else param
            return await manager.add_or_update(template, keep_key=keep_key)

    if 'update' not in exclude:

        @router.post("/update")
        async def update(request: Request) -> dict:
            param = await request_body(request, False)
            template = protobuf_transformer.dict_to_protobuf(param, pb) if pb else param
            return manager.add_or_update(template, keep_key=keep_key)

    if 'delete' not in exclude:

        @router.delete("/delete/{id}")
        async def delete(id: str) -> int:
            return await manager.delete(id)


class BaseRouter:

    @property
    def router(self):
        return self._router

    def __init__(self,
                 router: APIRouter,
                 manager: CommonDAHelper,
                 pb: object = None,
                 keep_key: bool = False,
                 default_matcher: Callable = None,
                 exclude: list = ['delete']) -> None:
        self._router = router
        self._router.default_response_class = UJSONResponse
        add_route(router, manager, pb, keep_key, default_matcher, exclude)


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
