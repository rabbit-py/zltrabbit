# -*- coding: utf-8 -*-

from typing import Any

from fastapi import HTTPException, Request, status
from base.coroutine.context import context
from base.di.service_location import config


class RequestContext:

    def get(self) -> Request:
        return context.get('request')

    def set(self, request: Request) -> None:
        context.set('request', request)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.get(), name)


request_context = RequestContext()