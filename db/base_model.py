# -*- coding: utf-8 -*-

from base.di.service_location import service
from base.functions import to_lower_camel, to_snake
from base.util import date_utils


class BaseModel:
    STYLE_NONE = 0
    STYLE_SNAKE = 1
    STYLE_LOWER_CAMEL = 2

    def __init__(self, key_style=STYLE_NONE, key: str = 'id') -> None:
        self.__key_style = key_style
        self.__key = key
        self._id_generator = service.id_generator

    @property
    def key(self) -> str:
        return self.__key

    @property
    def key_style(self) -> int:
        return self.__key_style

    @property
    def data(self) -> dict:
        return self.__data

    def load(self, data: dict) -> 'BaseModel':
        match self.__key_style:
            case self.STYLE_LOWER_CAMEL:
                self.__data = to_lower_camel(data)
            case self.STYLE_NONE:
                self.__data = to_snake(data)
            case self.STYLE_NONE:
                self.__data = data

        return self

    def copy(self) -> 'BaseModel':
        return BaseModel(self.__key_style)

    def to_dict(self) -> dict:
        keep_key = self.key_style != self.STYLE_LOWER_CAMEL
        pb_tmp = {self.key: self.data.pop(self.key, None)}
        create_time_key = 'create_time' if keep_key and 'create_time' in self.data else 'createTime'
        self.data.pop(create_time_key, None)
        if not pb_tmp.get(self.key):
            pb_tmp.update({self.key: self._id_generator.generate_id()})
        time = date_utils.timestamp_second()
        pb_tmp.update({create_time_key: time})
        self.data.update({'update_time' if keep_key and 'update_time' in self.data else 'updateTime': time})
        return pb_tmp
