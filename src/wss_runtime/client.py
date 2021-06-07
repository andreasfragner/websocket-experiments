# -*- coding: utf-8 -*-
# __COPYRIGHT__
"""
Summary
-------
Usage ..code::

    init(host='localhost', port=8765)

    def foo(a, b=2):
        return a**2 + b

    def bar(a, b=2):
        raise RuntimeError("Failed")

    future = call(foo, 2, b=3)
    asyncio.run(future) # returns `7`

    futures = list(map(lambda x: call(foo, x), range(5)))
    results = get(futures) # returns `[2, 3, 6, 11, 18]`

    future = call(bar, 2, b=3)
    asyncio.run(future) # raises `TaskExecutionError`

"""

import asyncio
from typing import Any, Awaitable, Callable, Iterable

import websockets

from wss_runtime.common import TaskExecutionError, deserialize, serialize


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
        message = await websocket.recv()

        results = deserialize(message)

        if isinstance(results, TaskExecutionError):
            raise results

        return results


def get(futures: Iterable[Awaitable]) -> Iterable[Any]:
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(asyncio.gather(*futures))
