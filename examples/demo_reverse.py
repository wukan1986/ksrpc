"""
反弹RPC示例
"""
import asyncio

from ksrpc.connections.websocket import WebSocketConnection
from ksrpc.rpc_client import RpcClient

TOKEN = 'secret-token-1'
URL = 'ws://127.0.0.1:8000/ws/admin?room=HA9527'


async def async_main():
    # 连接控制端地址（带/admin），同时还要指定约定的房间号
    async with WebSocketConnection(URL, token=TOKEN) as conn:
        conn.timeout = (5, 90)

        demo = RpcClient('demo', conn, async_local=False)
        demo.cache_get = False
        demo.cache_expire = 60
        print(demo.sync_say_hi("AA"))
        for i in range(100):
            print(demo.test(i).head(1))


asyncio.run(async_main())
