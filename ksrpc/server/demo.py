"""
演示函数
"""
import asyncio
import time

import pandas as pd


def sync_say_hi(name):
    time.sleep(5)
    return f'Hello {name}'


async def async_say_hi(name):
    await asyncio.sleep(5)
    return f'Hello {name}'


def div(a, b):
    return a / b


def test():
    return pd._testing.makeTimeDataFrame()


def __call__(*args, **kwargs):
    print(args, kwargs, 1111111)
    pass
