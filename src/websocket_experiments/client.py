# -*- coding: utf-8 -*-
# __COPYRIGHT__
"""
Summary
-------
"""

__author__ = 'andreasfragner'
__contributors__ = [__author__]

import asyncio
import logging
from typing import Any, Awaitable, Callable

import websockets

from .common import deserialize, serialize

logger = logging.getLogger('websockets')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


async def call(fn: Callable, *args, **kwargs) -> Awaitable[Any]:
    """
    Submit function `fn` for remote execution with arguments `args` and `kwargs`
    """
    async with websockets.connect(URI) as websocket:

        task = serialize(fn, *args, **kwargs)
        await websocket.send(task)
        results = await websocket.recv()

        return deserialize(results)


def get(future: Awaitable,timeout: int =30.0) -> Any:
    return await asyncio.wait_for(future, timeout=timeout)


# def map(fn: Callable, args: Iterable) -> Iterable[Any]:
#     pass
