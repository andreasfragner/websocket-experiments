# -*- coding: utf-8 -*-
# __COPYRIGHT__
"""

"""

__author__ = "andreasfragner"
__contributors__ = [__author__]


import logging
from typing import ByteString, Callable, Dict, Tuple

import dill


def serialize(fn: Callable, *args, **kwargs) -> ByteString:
    return dill.dumps((fn, args, kwargs))


def deserialize(payload: ByteString) -> Tuple[Callable, Tuple, Dict]:
    return dill.loads(payload)


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
