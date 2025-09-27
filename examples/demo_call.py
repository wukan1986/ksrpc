import asyncio

from examples.config import USERNAME, PASSWORD, URL_HTTP, URL_WS  # noqa
from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection


async def async_main():
    async with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        server = RpcClient('ksrpc.server', conn, lazy=True)
        demo = server.demo
        print(await demo.test().collect_async())
        print(await demo.test().__len__().collect_async())

        print(await demo.div(demo.create_1d_array(target_mb=1), 0.01).collect_async())



asyncio.run(async_main())
