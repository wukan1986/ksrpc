import asyncio

from examples.config import USERNAME, PASSWORD, URL_HTTP, URL_WS  # noqa
from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection


async def async_main():
    # 注意：生成的代码需要再人工调整一下
    async with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        with open("uuid.pyi", 'w') as f:
            demo = RpcClient('uuid', conn, lazy=True)
            f.write(await demo.generate_stub().collect_async())

        with open("client.pyi", 'w') as f:
            demo = RpcClient('ksrpc.client', conn)
            f.write(await demo.generate_stub())


asyncio.run(async_main())
