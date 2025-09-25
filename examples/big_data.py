"""
使用WebSocket服务示例
"""
import asyncio

from examples.config import USERNAME, PASSWORD, URL_HTTP, URL_WS  # noqa
from ksrpc.client import RpcProxy
from ksrpc.connections.http import HttpConnection  # noqa
from ksrpc.connections.websocket import WebSocketConnection  # noqa


async def async_main():
    async with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        demo = RpcProxy('ksrpc.server.demo', conn)
        ret = await demo.create_1d_array(10)
        print(ret)

    async with WebSocketConnection(URL_WS, username=USERNAME, password=PASSWORD) as conn:
        demo = RpcProxy('ksrpc.server.demo', conn)
        ret = await demo.create_1d_array(10)
        print(ret)


asyncio.run(async_main())
