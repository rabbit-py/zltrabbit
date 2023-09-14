# -*- coding: utf-8 -*-

from base.di.service_location import config, service
from base.functions import to_lower_camel, to_snake
from base.util import date_utils


class BaseModel:
    STYLE_NONE = 'NONE'
    STYLE_SNAKE = 'SNAKE'
    STYLE_LOWER_CAMEL = 'LOWER_CAMEL'

    def __init__(self, key_style=None, use_time=True, key: str = 'id') -> None:
        self._key_style = key_style or config('model_key_style', self.STYLE_NONE)
        self._key = key
        self._use_time = use_time
        self._id_generator = service.id_generator

    @property
    def key(self) -> str:
        return self._key

    @property
    def key_style(self) -> int:
        return self._key_style

    @property
    def data(self) -> dict:
        return self._data

    def load(self, data: dict) -> 'BaseModel':
        match self._key_style:
            case self.STYLE_LOWER_CAMEL:
                self._data = to_lower_camel(data)
            case self.STYLE_SNAKE:
                self._data = to_snake(data)
            case self.STYLE_NONE:
                self._data = data

        return self

    def copy(self) -> 'BaseModel':
        return BaseModel(self._key_style)

    def to_dict(self) -> dict:
        keep_key = self._key_style != self.STYLE_LOWER_CAMEL
        pb_tmp = {self._key: self._data.pop(self._key, self._id_generator.generate_id())}
        if self._use_time:
            create_time_key = 'create_time' if keep_key and 'create_time' in self._data else 'createTime'
            self._data.pop(create_time_key, None)
            time = date_utils.timestamp_second()
            pb_tmp.update({create_time_key: time})
            self._data.update({'update_time' if keep_key and 'update_time' in self._data else 'updateTime': time})
        return pb_tmp
