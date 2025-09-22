"""
动态URL
"""
import asyncio
import time

from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection
from ksrpc.connections.websocket import WebSocketConnection
from ksrpc.utils.urls import TimeURL, BaseURL


async def async_main():
    async with HttpConnection(BaseURL("http://127.0.0.1:8080/api/file"), username="admin", password="password123") as conn:
        demo = RpcClient('ksrpc.server.demo', conn)
        print(await demo.__file__())

    # TODO 注意先修改coonf.py
    async with HttpConnection(TimeURL("http://127.0.0.1:8080/api/{}"), username="admin", password="password123") as conn:
        demo = RpcClient('ksrpc.server.demo', conn)
        print(await demo.__file__())
        time.sleep(10)
        print(await demo.__file__())

    # TODO 注意先修改coonf.py
    async with WebSocketConnection(TimeURL("ws://127.0.0.1:8080/ws/{}"), username="admin", password="password123") as conn:
        demo = RpcClient('ksrpc.server.demo', conn)
        print(await demo.__file__())
        time.sleep(10)
        print(await demo.__file__())


asyncio.run(async_main())
