"""
使用HTTP服务示例
"""
import asyncio

from ksrpc.client import RpcClient, RpcProxy
from ksrpc.connections.http import HttpConnection

URL = 'http://127.0.0.1:8080/api/file'


async def async_main():
    async with HttpConnection(URL, username="admin", password="password123") as conn:
        demo = RpcClient('ksrpc.server.demo', conn)
        ret = await demo.test()
        print(ret)

        # gather中不能用RpcClient，methods会混乱
        ret = await asyncio.gather(demo.sync_say_hi("AA"),
                                   demo.async_say_hi("BB"),
                                   demo.sync_say_hi("CC"))
        print(ret)

        # gather中要换成RpcProxy
        demo = RpcProxy('ksrpc.server.demo', conn)
        ret = await asyncio.gather(demo.sync_say_hi("AA"),
                                   demo.async_say_hi("BB"),
                                   demo.sync_say_hi("CC"))
        print(ret)


asyncio.run(async_main())
