"""
使用WebSocket服务示例
"""
import asyncio

from ksrpc.client import RpcProxy, RpcClient
from ksrpc.connections.websocket import WebSocketConnection

URL = 'ws://127.0.0.1:8080/ws/file'


async def async_main():
    async with WebSocketConnection(URL, username="admin", password="password123") as conn:
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
