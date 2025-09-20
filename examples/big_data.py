"""
使用WebSocket服务示例
"""
import asyncio

from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection  # noqa
from ksrpc.connections.websocket import WebSocketConnection  # noqa

URL = 'ws://127.0.0.1:8080/ws/file'


async def async_main():
    async with WebSocketConnection(URL, username="admin", password="password123") as conn:
        demo = RpcClient('ksrpc.server.demo', conn)
        ret = await demo.create_1d_array(200)
        print(ret)


asyncio.run(async_main())
