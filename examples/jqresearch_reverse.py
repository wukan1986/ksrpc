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

        jq = RpcClient('jqresearch', conn, async_local=False)
        jq.cache_get = False
        jq.cache_expire = 60
        print(jq.api.get_price('000001.XSHE'))
        print(jq.api.get_ticks("000001.XSHE", start_dt=None, end_dt="2018-07-02", count=10))

        # StateException('Interruptingcow can only be used from the MainThread.',)
        # 由于query相关操作无法异步，所以只能指定async_remote=False
        jqr = RpcClient('jqresearch_query', conn, async_local=False, async_remote=False)
        jqr.cache_get = False
        jqr.cache_expire = 60
        print(jqr.get_fundamentals_valuation('2015-10-15'))


asyncio.run(async_main())
