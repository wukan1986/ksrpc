"""
使用WebSocket服务示例
"""
import asyncio

from examples.config import USERNAME, PASSWORD, URL_HTTP, URL_WS  # noqa
from ksrpc.client import RpcProxy
from ksrpc.connections.websocket import WebSocketConnection


async def async_main():
    async with WebSocketConnection(URL_WS, username=USERNAME, password=PASSWORD) as conn:
        # gather中要换成RpcProxy
        demo = RpcProxy('ksrpc.server.demo', conn)
        ret = await asyncio.gather(demo.sync_say_hi("AA"),
                                   demo.async_say_hi("BB"),
                                   demo.sync_say_hi("CC"))
        print(ret)

        ret = await demo.test()
        print(ret)


asyncio.run(async_main())
