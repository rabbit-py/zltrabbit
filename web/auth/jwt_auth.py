# -*- coding: utf-8 -*-

import datetime
import time
from typing import Any
import jwt
from .user_context import user_context


class JwtAuth:
    def __init__(self, issuer: str, secret: str, expired: int = 86400) -> None:
        self._issuer = issuer
        self._secret = secret
        self._expired = expired

    def encode_token(self, user_info: dict, expired: int = None) -> str:
        config = {}
        if expired == 0:
            config.update({'iss': self._issuer})
        elif isinstance(expired, int) and expired > 0:
            config.update({'exp': datetime.datetime.now() + datetime.timedelta(seconds=expired), 'iss': self._issuer})
        else:
            config.update(
                {
                    'exp': datetime.datetime.now() + datetime.timedelta(seconds=self._expired),
                    'iss': self._issuer,
                }
            )
        config.update({'data': user_info})
        return jwt.encode(config, self._secret, algorithm='HS256')

    def decode_token(self, token: str) -> dict:
        try:
            user = jwt.decode(token, self._secret, issuer=self._issuer, algorithms=['HS256'], options={'verify_exp': False})
            user_context.set(user)
        except Exception:
            return None
        return user

    def check_token(self, token: str) -> bool:
        decode_token = self.decode_token(token)
        return decode_token and (decode_token.get('exp') is None or decode_token.get('exp') > int(time.time()))

    def get_token_data(self, token: str, key: str = None) -> Any:
        data = self.decode_token(token).get('data', {})
        if key:
            if isinstance(key, list):
                ret = {}
                for x in key:
                    ret.update({x: data.get(x)})
                return ret
            return data.get(key)
        return data
