"""
生成器，迭代器的用法
"""
import asyncio

from examples.config import USERNAME, PASSWORD, URL_HTTP, URL_WS  # noqa
from ksrpc.client import RpcClient, rpc_iterator
from ksrpc.connections.http import HttpConnection


async def async_main():
    async with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        demo = RpcClient('ksrpc.server.demo', conn)

        # 以异步方法调用远程的异步迭代函数
        async for it in rpc_iterator(demo.async_counter()):
            print(it)

        # 以异步方法调用远程的同步迭代函数
        async for it in rpc_iterator(demo.sync_counter()):
            print(it)

        gen = await demo.async_counter()
        # TODO 为何__next__要两层括号？
        print(await gen.__next__()())
        # TODO 为何__anext__要这么写？能简化吗?
        print(await (await gen.__anext__())())
        print(await gen.__next__()())
        print(await gen.__next__()())  # StopAsyncIteration


asyncio.run(async_main())
