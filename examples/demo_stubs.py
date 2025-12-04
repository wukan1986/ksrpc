"""
服务端需要 pip install mypy
或 pip install ksrpc[stub]
"""
import asyncio

from examples.config import USERNAME, PASSWORD, URL_HTTP, URL_WS  # noqa
from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection


async def async_main():
    # 注意：生成的代码需要再人工调整一下
    async with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        demo = RpcClient('ksrpc', conn)
        output = await demo.generate_stub()
        print(output)

        demo = RpcClient('uuid', conn, lazy=True)
        output = await demo.generate_stub().collect()
        print(output)
        # with open("uuid.pyi", 'w') as f:
        #     f.write(output)

        demo = RpcClient('ksrpc.client', conn)
        output = await demo.generate_stub()
        print(output)
        # with open("client.pyi", 'w') as f:
        #     f.write(output)


asyncio.run(async_main())
