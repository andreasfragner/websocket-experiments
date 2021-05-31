# -*- coding: utf-8 -*-
# __COPYRIGHT__
"""
Summary
-------
Usage ..code::

    init(port=8765)
    call(foo, 2, b=3)
"""

__author__ = "andreasfragner"
__contributors__ = [__author__]

import asyncio
import logging
from typing import Any, Awaitable, Callable

import websockets

from .common import deserialize, serialize

logger = logging.getLogger("websockets")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def init(host: str = "localhost", port: int = 8765) -> None:
    global WS_SERVER_URI
    WS_SERVER_URI = f"ws://{host}:{port}"


async def call(fn: Callable, *args, **kwargs) -> Any:
    """
    Submit function `fn` for remote execution with arguments `args` and `kwargs`
    """
    async with websockets.connect(WS_SERVER_URI) as websocket:

        task = serialize((fn, args, kwargs))
        await websocket.send(task)
        results = await websocket.recv()

        return deserialize(results)


# def get(future: Awaitable,timeout: int =30.0) -> Any:
#     # or asyncio.run()
#     return await asyncio.wait_for(future, timeout=timeout)


# def map(fn: Callable, args: Iterable) -> Iterable[Any]:
#     pass
