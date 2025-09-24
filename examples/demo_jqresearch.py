"""
使用HTTP服务示例
"""
import asyncio

from examples.config import USERNAME, PASSWORD, URL_HTTP, URL_WS  # noqa
from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection


async def async_main():
    async with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        jqresearch = RpcClient('jqresearch', conn)
        print(await jqresearch.api.get_price(security='000001.XSHE'))

        api = RpcClient('jqresearch.api', conn)
        print(await api.get_price(security='000001.XSHE'))


asyncio.run(async_main())
