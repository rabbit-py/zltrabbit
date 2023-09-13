# -*- coding: utf-8 -*-

import inspect
from fastapi import FastAPI, status
from starlette.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from base.functions import env
from base.di.service_location import service
from web.middleware.request_context_middleware import RequestContextMiddleware
from web.routes.base_router import JSONResponse
from web.routes.base_router import auto_import


def register_base(app: FastAPI, before_import: list = [], after_import: list = []) -> None:
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

    @app.on_event("startup")
    async def startup_event():
        service.refresh()
        for func in before_import:
            if inspect.isfunction(func):
                await func() if inspect.iscoroutinefunction(func) else func()
            elif isinstance(func, tuple):
                await func[0](**func[1]) if inspect.iscoroutinefunction(func[0]) else func[0](**func[1])

        auto_import(env('ROUTE_PATH'), app)
        for func in after_import:
            if inspect.isfunction(func):
                await func() if inspect.iscoroutinefunction(func) else func()
            elif isinstance(func, tuple):
                await func[0](**func[1]) if inspect.iscoroutinefunction(func[0]) else func[0](**func[1])
