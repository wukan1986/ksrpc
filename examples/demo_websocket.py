"""
使用WebSocket服务示例
"""
import asyncio

from ksrpc.client import RpcClient
from ksrpc.connections.websocket import WebSocketConnection

URL = 'ws://127.0.0.1:8080/ws/file'


async def async_main():
    async with WebSocketConnection(URL, username="admin", password="password123") as conn:
        demo = RpcClient('demo', conn)
        print(await demo.sync_say_hi("AA"))
        print(await demo.test())


asyncio.run(async_main())
