# -*- coding: utf-8 -*-
# __COPYRIGHT__
"""

"""

import logging
from typing import Any, ByteString, Callable, Dict, Tuple

import cloudpickle


def serialize(obj: Any) -> ByteString:
    return cloudpickle.dumps(obj)


def deserialize(payload: ByteString) -> Tuple[Callable, Tuple, Dict]:
    return cloudpickle.loads(payload)


class TaskExecutionError(Exception):
    pass


def configure_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s", datefmt="%H:%M:%S"
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
