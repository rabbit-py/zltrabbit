# -*- coding: utf-8 -*-

import sys
from loguru import logger
from uuid import uuid1

from base.functions import env
from base.logger.filter_interface import FilterInterface

from ..coroutine.context import context
from ..di.service_location import service


class LoggerFilter(FilterInterface):
    def filter(self, record: dict) -> bool:
        try:
            message_uuid = context.get('message_id')
        except Exception:
            pass
        if not message_uuid:
            message_uuid = uuid1().hex
            context.set('message_id', message_uuid)
        record["extra"]["request_id"] = message_uuid
        return True


def loguru_setup() -> None:
    config = service.config('logger', {})
    custom_format = config.get(
        'format',
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {extra[request_id]} | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
    )
    sys.tracebacklimit = config.get('tracebacklimit', None if env('DEBUG') else 2)
    logger.remove()
    logger.add(
        sys.stderr,
        format=custom_format,
        level=config.get('level', 'DEBUG' if env('DEBUG') else 'INFO'),
        enqueue=config.get('enqueue', True),
        filter=service.create(config.get('filter'), {}, False).filter if config.get('filter') else LoggerFilter().filter,
    )
