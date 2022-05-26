"""
使用HTTP服务示例
"""
import asyncio

from ksrpc.connections.http import HttpxConnection
from ksrpc.rpc_client import RpcClient

URL = 'http://127.0.0.1:8000/api/file'


def sync_main():
    with HttpxConnection(URL, token=None) as conn:
        conn.timeout = (5, 30)
        demo = RpcClient('demo', conn, is_async=False)
        demo.cache_get = True
        demo.cache_expire = 0
        print(demo.sync_say_hi("AA"))
        print(demo.test())
        print(demo.sync_say_hi("AA"))


async def async_main():
    async with HttpxConnection(URL, token='secret-token-1') as conn:
        conn.timeout = (5, 90)
        demo = RpcClient('demo', conn, is_async=True)
        demo.cache_get = True
        demo.cache_expire = 60

        ret = await asyncio.gather(demo.sync_say_hi("AA"), demo.async_say_hi("BB"), demo.sync_say_hi("CC"))
        print(ret)


asyncio.run(async_main())
sync_main()
