# -*- coding: utf-8 -*-

import importlib
import os
import re
import yaml
from typing import Any
from ..functions import env


class ServiceLocation:
    def __init__(self, path: str = 'configs') -> None:
        self.path = path
        self.configs = {}
        self.sl_map = {}
        self.refresh()

    def __getattr__(self, key: str) -> Any:
        return self.get(key)

    def refresh(self, path: str = None) -> None:
        if path is None:
            path = self.path
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if os.path.isdir(file_path):
                self.refresh(file_path)
            else:
                with open(file_path, mode='r', encoding='utf-8') as f:
                    data = yaml.load(stream=f, Loader=yaml.FullLoader)
                    self.configs = dict(self.configs, **data)

    def get(self, name: str, data: dict = {}, only_config: bool = False) -> Any:
        if only_config:
            return self.configs.get(name)
        if not self.sl_map.get(name):
            data = data or self.configs.get(name)
            module = data.get('()')
            if module:
                self.sl_map.update({name: self.build_class(module, data)})
        elif data:
            raise Exception(f'Service {name} already exists')

        return self.sl_map.get(name)

    def config(self, name: str, default: Any = None) -> Any:
        data = self.get(name, only_config=True)
        if data is None:
            return default
        return data

    def create(self, module: str, config_value: dict, single: bool = True) -> Any:
        if single:
            return self.get(module, config_value)
        else:
            return self.build_class(module, config_value)

    def build_class(self, module: str, config_value: dict) -> object:
        module, tmp_class = module.rsplit('.', 1)
        tmp_class = getattr(importlib.import_module(module), tmp_class)
        args = {}
        if hasattr(tmp_class.__init__, '__code__'):
            total_args = len(tmp_class.__init__.__code__.co_varnames)
            default_args = len(tmp_class.__init__.__defaults__) if tmp_class.__init__.__defaults__ is not None else 0
            for i, arg in enumerate(tmp_class.__init__.__code__.co_varnames):
                if arg != 'self':
                    arg_config = config_value.get(
                        arg,
                        tmp_class.__init__.__defaults__[i - total_args + default_args]
                        if default_args > 0 and i >= total_args - default_args
                        else None,
                    )
                    args.update(
                        {
                            arg: self.build_value(arg_config)
                            if not isinstance(arg_config, dict) or not arg_config.get('()')
                            else self.build_class(arg_config.get('()'), arg_config)
                        }
                    )
        tmp_object = tmp_class(**args)
        for p_name, p_value in config_value.items():
            if p_name == '()' or p_name in args:
                continue
            p_value = self.build_value(p_value)
            if hasattr(tmp_object, p_name):
                setattr(tmp_object, p_name, p_value)
            else:
                tmp_object.__dict__[p_name] = p_value
        return tmp_object

    def build_value(self, p_value: Any) -> Any:
        if isinstance(p_value, str) and ('config(' in p_value or 'get(' in p_value or 'env(' in p_value):
            p = re.compile(r'[(](.*?)[)]', re.S)
            items = re.findall(p, p_value).pop(0).split(',')
            name = items.pop(0).strip()
            if 'config(' in p_value:
                p_value = self.config(name)
                for key in items:
                    p_value = p_value.get(key.strip())
            elif 'get(' in p_value:
                p_value = self.get(name)
                while len(items) > 0:
                    name = items.pop(0).strip()
                    p_value = p_value.__dict__.get(name, p_value.__getattribute__(name))
            elif 'env(' in p_value:
                p_value = env(name)
        return p_value


service = ServiceLocation(env('CONFIG_PATH', 'configs'))


def config(name: str, default: Any = None) -> Any:
    return service.config(name, default)


class BaseService:
    def __getattr__(self, key: str) -> Any:
        if key in self.__dict__:
            return self.__dict__[key]

    def __setattr__(self, key: str, value: Any) -> None:
        self.__dict__[key] = value
