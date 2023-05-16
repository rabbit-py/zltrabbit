# -*- coding: utf-8 -*-
"""用于函数执行时间自动计时并通过日志输出的decorator。示例:
  from base.system.function_timer import function_timer

  @function_timer(name='YourFunction')
  def func():
      xxx
"""

import re
from loguru import logger
from .util.datetime_utils import DateTime

import os
from typing import Any, Callable


def env(key: str, default: Any = None) -> Any:
    value = os.environ.get(key)
    if value is None:
        return default
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


def turn_param_style(params: dict) -> dict:
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
        temp_dict.update({new_name.lower(): value})

    return temp_dict