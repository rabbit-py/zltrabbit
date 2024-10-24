# -*- coding: utf-8 -*-
"""用于函数执行时间自动计时并通过日志输出的decorator。示例:
  from base.system.function_timer import function_timer

  @function_timer(name='YourFunction')
  def func():
      xxx
"""

import asyncio
from contextlib import asynccontextmanager
import re
from loguru import logger
from .util.datetime_utils import DateTime

import os
from typing import Any, Awaitable, Callable, Union

from passlib.context import CryptContext


def env(key: str, default: Any = None) -> Any:
    value = os.environ.get(key)
    if value is None:
        return default
    elif value == 'false':
        return False
    elif value == 'true':
        return True
    return value


def function_timer(name: str = None) -> Callable:
    def decorator(func):
        def wrapper_function(*args, **kwargs):
            start = DateTime()
            result = func(*args, **kwargs)
            milliseconds = DateTime().milliseconds - start.milliseconds
            func_name = name
            if func_name is None:
                func_name = f'{func.__name__!r}'
            logger.info('[{}]  函数执行时间: {}毫秒'.format(func_name, milliseconds))
            return result

        return wrapper_function

    return decorator


def to_snake(params: dict, all: bool = True) -> dict:
    '''
    将参数名的驼峰形式转为下划线形式
    @param params:
    @return:
    '''
    temp_dict = {}
    for name, value in params.items():
        new_name = name
        if '_' not in name:
            new_name = re.sub(r'([a-z])([A-Z])', r'\1_\2', name)
        temp_dict.update({new_name.lower(): to_snake(value) if all and isinstance(value, dict) else value})

    return temp_dict


def to_lower_camel(params: dict, all: bool = True):
    """下划线转小驼峰法命名"""
    temp_dict = {}
    for name, value in params.items():
        new_name = re.sub('_([a-zA-Z])', lambda m: (m.group(1).upper()), name)
        temp_dict.update({new_name: to_lower_camel(value) if all and isinstance(value, dict) else value})

    return temp_dict


def encryption_password_or_decode(pwd: str, hashed_password: str = None) -> Union[str, bool]:
    """
    密码加密或解密
    :param pwd:
    :param hashed_password:
    :return:
    """
    encryption_pwd = CryptContext(schemes=["sha256_crypt", "md5_crypt", "des_crypt"])

    def encryption_password():
        password = encryption_pwd.hash(pwd)
        return password

    def decode_password():
        password = encryption_pwd.verify(pwd, hashed_password)
        return password

    return decode_password() if hashed_password else encryption_password()


async def wrap_done(fn: Awaitable, event: asyncio.Event, reraise: bool = None) -> Any:
    try:
        return await fn
    except Exception as e:
        logger.error(e)
        if reraise or env('DEBUG', True):
            raise e
    finally:
        event.set()


@asynccontextmanager
async def with_logger(reraise: bool = True) -> Any:
    try:
        yield
    except Exception as e:
        logger.error(e)
        if reraise:
            raise e
