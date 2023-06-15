# -*- coding: utf-8 -*-

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from base.coroutine.context import context
from base.di.service_location import service
from base.functions import env
from web.routes.base_router import UJSONResponse
from web.routes.request_context import request_context


class RequestContextMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        context.set('message_id', service.id_generator.generate_id())
        request_context.set(request)
        try:
            response = await call_next(request)
        except Exception as e:
            return UJSONResponse(status_code=500, code=500, msg=str(e) if env('DEBUG') else 'Internal Server Error')
        return response