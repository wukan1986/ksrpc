"""
反弹RPC示例
用反弹方法下载数据
"""
import asyncio

from ksrpc.connections.websocket import WebSocketConnection
from ksrpc.rpc_client import RpcClient

URL = 'ws://127.0.0.1:8000/ws/admin?room=9527'


async def async_main():
    # 连接控制端地址（带/admin），同时还要指定约定的房间号
    async with WebSocketConnection(URL) as conn:
        conn.timeout = (5, 90)

        jq = RpcClient('jqresearch', conn, is_async=False)
        jq.cache_get = False
        jq.cache_expire = 60
        print(jq.api.get_price('000001.XSHE'))
        print(jq.api.get_ticks("000001.XSHE", start_dt=None, end_dt="2018-07-02", count=10))


asyncio.run(async_main())
