# -*- coding: utf-8 -*-

import inspect
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from starlette.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from base.functions import env
from base.di.service_location import service
from base.util.wraps import event
from web.middleware.request_context_middleware import RequestContextMiddleware
from web.routes.base_router import JSONResponse
from web.routes.base_router import auto_import


class App:
    def app(self) -> FastAPI:
        return self._app

    def __init__(self, before_import: list = [], after_import: list = []) -> None:
        self._before_import = before_import
        self._after_import = after_import
        self._app = None

    def run(self, app: FastAPI) -> None:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=env("ALLOW_ORIGIN", "*").split(","),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        app.add_middleware(RequestContextMiddleware)

        @app.exception_handler(HTTPException)
        async def http_exception_handler(request, exc):
            return JSONResponse(status_code=exc.status_code, code=exc.status_code, msg=exc.detail)

        @app.exception_handler(RequestValidationError)
        async def request_exception_handler(request, exc):
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code=status.HTTP_422_UNPROCESSABLE_ENTITY, msg=str(exc)
            )

        self._app = app

    @asynccontextmanager
    async def liefspan(self, app: FastAPI) -> None:
        service.refresh()
        await self._event(self._before_import)
        auto_import(env('ROUTE_PATH'), app)
        await self._event(self._after_import)
        yield

    async def _event(self, events=[]) -> None:
        for func in events:
            if inspect.isfunction(func):
                await func() if inspect.iscoroutinefunction(func) else func()
            elif isinstance(func, tuple):
                await func[0](**func[1]) if inspect.iscoroutinefunction(func[0]) else func[0](**func[1])
