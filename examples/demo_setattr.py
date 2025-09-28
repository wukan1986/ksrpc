import asyncio

from examples.config import USERNAME, PASSWORD, URL_HTTP, URL_WS  # noqa
from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection


async def async_main():
    async with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        math = RpcClient('math', conn)
        print(await math.pi())  # math.pi
        print(await math.pi.__round__(4))  # round(math.pi, 4)

        demo = RpcClient('ksrpc.server.demo', conn)
        print(demo.__doc__)  # 取的其实是RpcClient的__doc__
        print(await demo.__getattr__('__doc__')())  # 取的远程ksrpc.server.demo.__doc__

        print(await demo.__getattr__('__setattr__')(
            'PASSWORD',
            await demo.PASSWORD() + 1
        ))  # 修改demo.PASSWORD
        print(await demo.PASSWORD())  # 只要server不重启就一直是新值

    async with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        math = RpcClient('math', conn, lazy=True)
        print(await math.pi.collect_async())  # math.pi
        print(await math.pi.__round__(4).collect_async())  # round(math.pi, 4)

        demo = RpcClient('ksrpc.server.demo', conn, lazy=True)
        print(demo.__doc__)  # 取的其实是RpcClient的__doc__
        print(await demo.__getattr__('__doc__').collect_async())  # 取的远程ksrpc.server.demo.__doc__

        print(await demo.__getattr__('__setattr__')(
            'PASSWORD',
            await demo.PASSWORD.collect_async() + 1
        ).collect_async())  # 修改demo.PASSWORD
        print(await demo.PASSWORD.collect_async())  # 只要server不重启就一直是新值


asyncio.run(async_main())
