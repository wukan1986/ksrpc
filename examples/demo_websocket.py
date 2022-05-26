"""
使用WebSocket服务示例
"""
import asyncio

from ksrpc.connections.websocket import WebSocketConnection
from ksrpc.rpc_client import RpcClient

TOKEN = 'secret-token-2'
URL = 'ws://127.0.0.1:8000/ws/bytes'


async def async_main():
    async with WebSocketConnection(URL, token=TOKEN) as conn:
        conn.timeout = (5, 90)

        demo = RpcClient('demo', conn, is_async=False)
        demo.cache_get = True
        demo.cache_expire = 60
        print(demo.sync_say_hi("AA"))
        print(demo.test())


def sync_main():
    with WebSocketConnection(URL, token=TOKEN) as client:
        client.timeout = (5, 90)

        demo = RpcClient('demo', client, is_async=False)
        demo.cache_get = True
        demo.cache_expire = 60
        print(demo.sync_say_hi("AA"))
        print(demo.test())


asyncio.run(async_main())
sync_main()
