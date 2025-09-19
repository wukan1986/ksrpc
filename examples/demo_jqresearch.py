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
        # 这两种写法，服务端收到的都是jqresearch.api.get_price
        # 都解析为jqresearch.api + get_price

        demo = RpcClient('jqresearch', conn)
        print(await demo.api.get_price(security='000001.XSHE'))

        demo = RpcClient('jqresearch.api', conn)
        print(await demo.get_price(security='000001.XSHE'))


asyncio.run(async_main())
