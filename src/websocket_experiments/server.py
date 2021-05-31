# -*- coding: utf-8 -*-
# __COPYRIGHT__
"""
Summary
-------
Simple websocket server implementing a producer-consumer pattern
"""

__author__ = "andreasfragner"
__contributors__ = [__author__]

import asyncio
import logging
from typing import (Any, Awaitable, ByteString, Callable, Dict, NoneType,
                    Optional, Tuple, Union)

import ray
import websockets
from websockets.server import WebSocketServer, WebSocketServerProtocol

from .common import configure_logging, deserialize, serialize

logger = logging.getLogger()


async def consumer(message: ByteString, queue: asyncio.Queue) -> None:
    task: Tuple[Callable, Tuple, Dict] = deserialize(message)
    await queue.put(task)


async def producer(queue: asyncio.Queue) -> Any:
    logger.info("Getting task for execution, %i items in queue", len(queue))
    fn, args, kwargs = await queue.get()
    func = ray.remote(fn)
    return await func(*args, **kwargs)


async def consumer_handler(
    websocket: WebSocketServerProtocol, queue: asyncio.Queue
) -> None:
    async for message in websocket:
        logger.info("Consuming message, %i items ahead in queue", len(queue))
        await consumer(message, queue)


async def producer_handler(
    websocket: WebSocketServerProtocol, queue: asyncio.Queue
) -> None:
    while True:
        result: Awaitable[Any] = await producer(queue)
        message: ByteString = serialize(result)
        websocket.send(message)


async def handler(websocket: WebSocketServerProtocol, path: Optional[str]) -> None:

    queue: asyncio.Queue = asyncio.Queue()

    consume = asyncio.ensure_future(consumer_handler(websocket, queue))
    produce = asyncio.ensure_future(producer_handler(websocket, queue))

    done, pending = await asyncio.wait(
        [consume, produce], return_when=asyncio.ALL_COMPLETED
    )

    for task in pending:
        task.cancel()


if __name__ == "__main__":

    WS_HOST: str = "localhost"
    WS_PORT: int = 8765
    WS_MAX_MESSAGE_SIZE: Union[int, NoneType] = None

    RAY_HOST: str = "localhost"
    RAY_PORT: int = 8001
    RAY_ADDRESS: str = f"{RAY_HOST}/{RAY_PORT}"

    ray.init(RAY_ADDRESS)

    # logger = logging.getLogger("websockets")
    # logger.setLevel(logging.INFO)
    # logger.addHandler(logging.StreamHandler())
    configure_logging(level="INFO")

    server: WebSocketServer = websockets.serve(
        handler, WS_HOST, WS_PORT, max_size=WS_MAX_MESSAGE_SIZE
    )

    logger.info("Start server")
    asyncio.get_event_loop().run_until_complete(server)
    logger.info("Running forever")
    asyncio.get_event_loop().run_forever()
