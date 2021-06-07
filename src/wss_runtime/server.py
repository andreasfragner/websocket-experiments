#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __COPYRIGHT__
"""
Summary
-------
Usage ..code::

    import ray, websockets
    from wss_runtime.server import handler

    ray.init(address=RAY_ADDRESS)

    server = websockets.serve(
        handler, WS_HOST, WS_PORT, max_size=WS_MAX_MESSAGE_SIZE
    )
    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()

"""

import asyncio
import logging
from typing import Any, Awaitable, ByteString, Callable, Dict, Optional, Tuple, Union

import ray
import websockets
from websockets.server import WebSocketServer, WebSocketServerProtocol

from wss_runtime.common import (
    TaskExecutionError,
    configure_logging,
    deserialize,
    serialize,
)

logger = logging.getLogger()


async def consumer(message: ByteString, queue: asyncio.Queue) -> None:
    task: Tuple[Callable, Tuple, Dict] = deserialize(message)
    await queue.put(task)


async def producer(queue: asyncio.Queue) -> Any:
    fn, args, kwargs = await queue.get()
    func = ray.remote(fn)
    return await func.remote(*args, **kwargs)


async def consumer_handler(
    websocket: WebSocketServerProtocol, queue: asyncio.Queue
) -> None:
    async for message in websocket:
        logger.debug("Got message (queue: %i, client: %s)", queue.qsize(), websocket)
        await consumer(message, queue)


async def producer_handler(
    websocket: WebSocketServerProtocol, queue: asyncio.Queue
) -> None:
    while True:
        try:
            result: Awaitable[Any] = await producer(queue)
        except Exception as ex:
            logger.exception(
                "Task execution failed, forwarding exception (client: %s)", websocket
            )
            result = TaskExecutionError(str(ex))

        message: ByteString = serialize(result)
        await websocket.send(message)
        logger.debug("Sent result (queue: %i, client: %s)", queue.qsize(), websocket)


async def handler(websocket: WebSocketServerProtocol, path: Optional[str]) -> None:

    queue: asyncio.Queue = asyncio.Queue(maxsize=64)

    consume: Awaitable = asyncio.ensure_future(consumer_handler(websocket, queue))
    produce: Awaitable = asyncio.ensure_future(producer_handler(websocket, queue))

    done, pending = await asyncio.wait(
        [consume, produce], return_when=asyncio.FIRST_COMPLETED
    )

    for task in pending:
        task.cancel()


if __name__ == "__main__":

    configure_logging(level="INFO")

    WS_HOST: str = "localhost"
    WS_PORT: int = 8765
    WS_MAX_MESSAGE_SIZE: Union[int, None] = None

    RAY_HOST: str = "localhost"
    RAY_PORT: int = 8001
    RAY_ADDRESS: str = f"{RAY_HOST}:{RAY_PORT}"

    ray.init(address=RAY_ADDRESS)

    server: WebSocketServer = websockets.serve(
        handler, WS_HOST, WS_PORT, max_size=WS_MAX_MESSAGE_SIZE
    )

    logger.info("Start server")
    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()
