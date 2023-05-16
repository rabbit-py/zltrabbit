# -*- coding: utf-8 -*-

from base.coroutine import context
from base.di.service_location import service


class UserContext:

    @property
    def id(self) -> str:
        return context.get('request_user', {}).get('data', {}).get(service.config('jwt').get('id', 'id'))

    def get(self) -> dict:
        return context.get('request_user', {}).get('data')

    def set(self, user: dict) -> None:
        context.set('request_user', user)


user_context = UserContext()