import asyncio

from examples.config import USERNAME, PASSWORD, URL_HTTP, URL_WS  # noqa
from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection

URL_HTTP = 'http://100.100.100.100:7001/api/v1/{time}'


async def async_main():
    async with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        api = RpcClient('jqresearch.api', conn)
        output = await api.generate_stub()
        print(output)
        print(await api.get_price(security='000001.XSHE'))

        # 需要先上传jqresearch_query.py
        query = RpcClient('jqresearch_query', conn, lazy=True)
        output = await query.generate_stub().collect_async()
        print(output)
        print(await query.get_fundamentals_valuation(date='2025-09-26').collect_async())


asyncio.run(async_main())
