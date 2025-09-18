"""
使用HTTP服务示例
"""
import asyncio

from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection

URL = 'http://127.0.0.1:8080/api/file'


async def async_main():
    async with HttpConnection(URL, username="admin", password="password123") as conn:
        demo = RpcClient('demo', conn)

        print(await demo.test())

        # gather中不能这么用
        ret = await asyncio.gather(demo.sync_say_hi("AA"),
                                   demo.async_say_hi("BB"),
                                   demo.sync_say_hi("CC"))
        print(ret)

        ret = await asyncio.gather(RpcClient('demo', conn).sync_say_hi("AA"),
                                   RpcClient('demo', conn).async_say_hi("BB"),
                                   RpcClient('demo', conn).sync_say_hi("CC"))
        print(ret)

        ret = await demo.test_array()
        print(ret)

        # ret = await demo.create_1d_array(1024 * 32)
        # print(ret)


asyncio.run(async_main())
