import asyncio

from examples.config import USERNAME, PASSWORD, URL_HTTP, URL_WS  # noqa
from ksrpc.client import RpcClient, Self
from ksrpc.connections.http import HttpConnection


async def async_main():
    async with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        # 同时存在demo属性和demo模块
        server = RpcClient('ksrpc.server', conn, lazy=True)
        print(await server.demo.collect())  # 取到是属性

        demo = RpcClient('ksrpc.server.demo', conn, lazy=True)
        print(await demo.collect())  # 取到的是模块

        print(await demo.test().collect())
        print(await demo.test().__len__().collect())
        print(await demo.div(demo.create_1d_array(target_mb=1), 0.01).collect())

        # 这种过于复杂的，建议用exec+eval，毕竟int(str)这种就没办法实现
        print(await (demo.PASSWORD.__getattr__('__str__')()[3].__add__("100")).collect())
        # 底层做了特别处理的实现str(Self)和int(Self)都是特别地方
        print(await (demo.PASSWORD.str(Self)[3].int(Self).__add__(100)).collect())
        # 比较复杂的func(Self)用法 str(pow(len(str(demo.PASSWORD)),len(str(demo.PASSWORD)))
        print(await (demo.PASSWORD.str(Self).len(Self).pow(Self, Self).str(Self)).collect())


asyncio.run(async_main())
