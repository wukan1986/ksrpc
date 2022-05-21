#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author     :wukan
# @License    :(C) Copyright 2022, wukan
# @Date       :2022-05-16

"""
同步与异步互转的小工具

FastAPI大量使用了async异步编程，如果内有阻塞函数或执行过久，将无法处理新请求
而大部分API都是同步阻塞模式，所以需要转异步

而在客户端，为了达到与原API一样，所以还需要有异步转同步功能

某些情况下需要nest_asyncio补丁才不会报错
"""
import asyncio
import inspect
from functools import partial, wraps

# 可能出现RuntimeError: This event loop is already running，所以打补丁
import nest_asyncio

nest_asyncio.apply()


def to_async(f):
    """同步转异步"""

    @wraps(f)
    async def decorated(*args, **kwargs):
        if inspect.iscoroutinefunction(f):
            # 已经是异步函数了就直接调用
            return await f(*args, **kwargs)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(f, *args, **kwargs))

    return decorated


def to_sync(f):
    """异步转同步"""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not inspect.iscoroutinefunction(f):
            # 已经是同步函数了就直接调用
            return f(*args, **kwargs)

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # RuntimeError: There is no current event loop in thread 'ThreadPoolExecutor-0_0'.
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # RuntimeError: This event loop is already running，某些情况下，需要nest_asyncio配合
        return loop.run_until_complete(f(*args, **kwargs))

    return decorated


if __name__ == '__main__':
    import time


    @to_async
    def do_sync_work(name: str):
        time.sleep(1)
        return f"同步 + 上加装饰器, {name}"


    async def do_async_work(name: str):
        await asyncio.sleep(1)
        return f"异步 + 不加装饰器, {name}"


    async def async_main():
        # 装饰器通常用法
        message = await do_sync_work(name="改异步")
        print(message)


    def sync_main():
        # 装饰器特殊用法
        message = to_sync(do_async_work)(name="改同步")
        print(message)


    asyncio.run(async_main())
    sync_main()


    async def async_main_2():
        # 套娃
        message = await to_async(to_sync(do_sync_work))(name="改")
        print(message)


    def sync_main_2():
        # 套娃
        message = to_sync(to_async(to_sync(do_sync_work)))(name="改")
        print(message)


    asyncio.run(async_main_2())
    sync_main_2()
