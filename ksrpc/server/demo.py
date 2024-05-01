"""
演示函数
"""
import asyncio
import time

import pandas as pd


def sync_say_hi(name):
    time.sleep(1)
    return f'Hello {name}'


async def async_say_hi(name):
    await asyncio.sleep(1)
    return f'Hello {name}'


def div(a, b):
    return a / b


def test(i):
    pd._testing._N = 10000
    pd._testing._K = 26
    return pd._testing.makeTimeDataFrame()


## 以下为python 3.6下module不支持__getattr__的处理方法，请按实际情况进行设置
import sys


class Wrapper(object):
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __getattr__(self, name):
        # Perform custom logic here
        try:
            return getattr(self.wrapped, name)
        except AttributeError as e:
            raise e


sys.modules[__name__] = Wrapper(sys.modules[__name__])
