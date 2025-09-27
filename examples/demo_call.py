import asyncio

from examples.config import USERNAME, PASSWORD, URL_HTTP, URL_WS  # noqa
from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection


async def async_main():
    async with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        server = RpcClient('ksrpc.server', conn)
        demo = server.demo
        print(await demo.test())
        print(await demo.test())

        demo = RpcClient('ksrpc.server.demo', conn)
        print(await demo.point.__format__("p"))  # format(ksrpc.server.demo.p, "p")
        print(await demo.point.__format__.__func__())  # ksrpc.server.demo.p.__format__.__func__
        print(await demo.point.__format__.__func__.__name__())  # ksrpc.server.demo.p.__format__.__func__.__name__

        print(await demo.create_1d_array(target_mb=1))

        await demo.div(1, 0)  # 测试服务端异常传到本地


asyncio.run(async_main())
