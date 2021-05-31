#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __COPYRIGHT__
"""
Summary
-------
Simple websocket server implementing a producer-consumer pattern to execute functions on
a ray cluster
"""

__author__ = "andreasfragner"
__contributors__ = [__author__]

import asyncio
import logging
from typing import (Any, Awaitable, ByteString, Callable, Dict, Optional,
                    Tuple, Union)

import ray
import websockets
from websocket_experiments.common import (TaskExecutionError,
                                          configure_logging, deserialize,
                                          serialize)
from websockets.server import WebSocketServer, WebSocketServerProtocol

logger = logging.getLogger()


async def consumer(message: ByteString, queue: asyncio.Queue) -> None:
    task: Tuple[Callable, Tuple, Dict] = deserialize(message)
    await queue.put(task)


async def producer(queue: asyncio.Queue) -> Any:
    logger.info("Getting task for execution, %i items in queue", queue.qsize())
    fn, args, kwargs = await queue.get()
    func = ray.remote(fn)
    return await func.remote(*args, **kwargs)


async def consumer_handler(
    websocket: WebSocketServerProtocol, queue: asyncio.Queue
) -> None:
    async for message in websocket:
        logger.info("Consuming message, %i items ahead in queue", queue.qsize())
        await consumer(message, queue)
        logger.info("Done consuming message")


async def producer_handler(
    websocket: WebSocketServerProtocol, queue: asyncio.Queue
) -> None:
    while True:
        try:
            result: Awaitable[Any] = await producer(queue)
        except Exception as ex:
            logger.exception("Task execution failed")
            result = TaskExecutionError(str(ex))

        logger.info("Got result from producer")
        message: ByteString = serialize(result)
        await websocket.send(message)
        logger.info("Sent result to client")


async def handler(websocket: WebSocketServerProtocol, path: Optional[str]) -> None:

    queue: asyncio.Queue = asyncio.Queue()

    consume: Awaitable = asyncio.ensure_future(consumer_handler(websocket, queue))
    produce: Awaitable = asyncio.ensure_future(producer_handler(websocket, queue))

    done, pending = await asyncio.wait(
        [consume, produce], return_when=asyncio.FIRST_COMPLETED
    )

    for task in pending:
        task.cancel()


if __name__ == "__main__":

    WS_HOST: str = "localhost"
    WS_PORT: int = 8765
    WS_MAX_MESSAGE_SIZE: Union[int, None] = None

    RAY_HOST: str = "localhost"
    RAY_PORT: int = 8001
    RAY_ADDRESS: str = f"{RAY_HOST}:{RAY_PORT}"

    ray.init(address=RAY_ADDRESS)

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
