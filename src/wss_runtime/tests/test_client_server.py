# -*- coding: utf-8 -*-
# __COPYRIGHT__
"""
"""

import asyncio
import threading
import time
from contextlib import contextmanager
from timeit import default_timer as timer

import pytest
import ray
import websockets

from wss_runtime.client import call, get, init
from wss_runtime.server import handler


@pytest.fixture(scope="module")
def ws_host():
    return "localhost"


@pytest.fixture(scope="module")
def ws_port():
    return 8675


def run_server(loop, server):
    loop.run_until_complete(server)
    loop.run_forever()


@pytest.fixture(scope="module", autouse=True)
def server(ws_host, ws_port):
    ray.init()
    init(host=ws_host, port=ws_port)

    loop = asyncio.new_event_loop()
    server = websockets.serve(handler, ws_host, ws_port, max_size=None, loop=loop)

    thread = threading.Thread(target=run_server, args=(loop, server), daemon=True)
    thread.start()

    time.sleep(2)
    yield


def fn_with_args(a):
    return a ** 2


def fn_with_kwargs(a, b=1):
    return a ** 2 + b


def fn_no_args():
    return 42


GLOBAL_VAR = 42


def fn_with_global_var(a):
    return a ** 2 + GLOBAL_VAR


def fn_with_delay(a, b=2, delay=0.1):
    time.sleep(delay)
    return a ** 2 + b


def fn_return_exception(message):
    return Exception(message)


def fn_raise_exception(message):
    raise fn_return_exception(message)


@pytest.fixture
def expected(fn, args, kwargs):
    return fn(*args, **kwargs)


def assert_equal(result, expected):
    if isinstance(expected, Exception):
        assert type(result) is type(expected) and result.args == expected.args
    else:
        assert result == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fn, args, kwargs",
    [
        (fn_no_args, (), {}),
        (fn_with_args, (0,), {}),
        (fn_with_args, (1,), {}),
        (fn_with_args, (2,), {}),
        (fn_with_kwargs, (0,), {"b": 0}),
        (fn_with_kwargs, (1,), {"b": 1}),
        (fn_with_kwargs, (2,), {"b": -1}),
        (fn_return_exception, ("failed",), {}),
        (fn_with_global_var, (1,), {}),
        (fn_with_global_var, (2,), {}),
        (lambda a, b: a ** 2 + b ** 2, (1, 2), {}),
    ],
)
def test_call(fn, args, kwargs, expected):
    result = asyncio.run(call(fn, *args, **kwargs))
    assert_equal(result, expected)


@pytest.mark.asyncio
@pytest.mark.parametrize("message", ["", "foo", "bar"])
def test_call_forwards_exceptions(message):
    with pytest.raises(Exception) as excinfo:
        asyncio.run(call(fn_raise_exception, message))
    assert message in str(excinfo.value)


@contextmanager
def timeit():
    start = timer()
    yield lambda: timer() - start


@pytest.mark.asyncio
@pytest.mark.parametrize("delay", [0.1, 0.25])
@pytest.mark.parametrize("args", [range(5), range(5, 10)])
def test_call_map(delay, args):

    with timeit() as elapsed:
        futures = list(map(lambda x: call(fn_with_delay, x, delay=delay), args))
        results = get(futures)
        elapsed_remote = elapsed()

    with timeit() as elapsed:
        expected = list(map(lambda x: fn_with_delay(x, delay=delay), args))
        elapsed_local = elapsed()

    assert results == expected
    assert elapsed_remote < elapsed_local
