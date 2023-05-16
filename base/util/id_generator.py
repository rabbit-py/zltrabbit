# -*- coding: utf-8 -*-

import abc
import uuid


class IdGeneratorInterface(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def generate_id(self):
        pass


class UUIDIdGenerator(IdGeneratorInterface):

    def generate_id(self, is_uppercase=False, with_hyphen=False):
        id = str(uuid.uuid4())
        if not with_hyphen:
            id = id.replace('-', '')
        if is_uppercase:
            id = id.upper()
        return id
