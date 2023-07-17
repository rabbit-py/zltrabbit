# -*- coding: utf-8 -*-

from fastapi import FastAPI, status
from starlette.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from base.functions import env
from base.di.service_location import service
from web.middleware.request_context_middleware import RequestContextMiddleware
from web.routes.base_router import UJSONResponse
from web.routes.base_router import auto_import


def register_base(app: FastAPI, *args) -> None:

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
        return UJSONResponse(status_code=exc.status_code, code=exc.status_code, msg=exc.detail)

    @app.exception_handler(RequestValidationError)
    async def request_exception_handler(request, exc):
        return UJSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code=status.HTTP_422_UNPROCESSABLE_ENTITY, msg=str(exc))

    @app.on_event("startup")
    def startup_event():
        service.refresh()
        for func in args:
            func()
        auto_import(env('ROUTE_PATH'), app)
