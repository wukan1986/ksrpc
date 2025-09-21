"""
使用WebSocket服务示例
"""
import asyncio

from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection  # noqa
from ksrpc.connections.websocket import WebSocketConnection  # noqa




async def async_main():
    URL = 'http://127.0.0.1:8080/api/file'
    async with HttpConnection(URL, username="admin", password="password123") as conn:
        demo = RpcClient('ksrpc.server.demo', conn)
        ret = await demo.create_1d_array(100)
        print(ret)

    URL = 'ws://127.0.0.1:8080/ws/file'
    async with WebSocketConnection(URL, username="admin", password="password123") as conn:
        demo = RpcClient('ksrpc.server.demo', conn)
        ret = await demo.create_1d_array(100)
        print(ret)


asyncio.run(async_main())
