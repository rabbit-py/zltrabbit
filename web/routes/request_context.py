# -*- coding: utf-8 -*-

from fastapi import Request
from base.coroutine.base_context import BaseContext
from base.coroutine.context import context

CONTEXT_KEY = 'request'


class RequestContext(BaseContext):

    def get(self) -> Request:
        return context.get(CONTEXT_KEY)

    def set(self, request: Request) -> None:
        context.set(CONTEXT_KEY, request)


request_context = RequestContext(CONTEXT_KEY)