# -*- coding: utf-8 -*-
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from base.coroutine.context import context
from base.di.service_location import service


class RequestContextMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        context.set('message_id', service.id_generator.generate_id())
        response = await call_next(request)
        return response