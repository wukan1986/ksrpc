"""
使用HTTP服务示例
"""
import asyncio

from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection

URL = 'http://127.0.0.1:8080/api/file'
URL = 'http://www.abc.com:7001/api/file'


async def async_main():
    async with HttpConnection(URL, username="admin", password="password123") as conn:
        jqresearch = RpcClient('jqresearch', conn)
        print(await jqresearch.api.get_price(security='000001.XSHE'))

        api = RpcClient('jqresearch.api', conn)
        print(await api.get_price(security='000001.XSHE'))


asyncio.run(async_main())
