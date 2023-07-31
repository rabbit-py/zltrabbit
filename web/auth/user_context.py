# -*- coding: utf-8 -*-

from typing import Any

from fastapi import HTTPException, status
from base.coroutine.context import context
from base.di.service_location import config


class UserContext:

    @property
    def id(self) -> str:
        id = context.get('request_user', {}).get('data', {}).get(config('jwt').get('id', 'id'))
        if not id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
        return id

    def get(self, key: str = None, default: Any = None) -> dict:
        data = context.get('request_user', {}).get('data', {})
        if key:
            return data.get(key, default)
        return data

    def set(self, user: dict) -> None:
        context.set('request_user', user)

    def remove(self) -> None:
        context.remove('request_user')

    def __getattr__(self, key) -> Any:
        return context.get('request_user', {}).get('data', {}).get(key)


user_context = UserContext()