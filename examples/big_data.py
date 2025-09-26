"""
使用WebSocket服务示例
"""
import asyncio

from examples.config import USERNAME, PASSWORD, URL_HTTP, URL_WS  # noqa
from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection  # noqa
from ksrpc.connections.websocket import WebSocketConnection  # noqa


async def async_main():
    from ksrpc.server.demo import create_1d_array
    a = create_1d_array(5)
    print(a)

    async with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        demo = RpcClient('ksrpc.server.demo', conn)
        ret = await demo.add(a, 1)
        print(ret)

    async with WebSocketConnection(URL_WS, username=USERNAME, password=PASSWORD) as conn:
        demo = RpcClient('ksrpc.server.demo', conn)
        ret = await demo.add(a, 2)
        print(ret)


asyncio.run(async_main())
