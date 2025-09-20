"""
常见的几种调用方法
"""
import asyncio

from ksrpc.client import RpcClient, RpcProxy
from ksrpc.connections.http import HttpConnection

URL = 'http://127.0.0.1:8080/api/file'


async def async_main():
    async with HttpConnection(URL, username="admin", password="password123") as conn:
        server = RpcClient('ksrpc.server', conn)
        print(await server.demo.test())
        server = RpcClient('ksrpc.server', conn)
        print(await server.demo.CLASS.D.C.__getitem__(2))

        demo = RpcClient('ksrpc.server.demo', conn)

        print(await demo.PASSWORD())
        print(await demo())

        demo = RpcProxy('ksrpc.server.demo', conn)
        print(await demo.__file__())
        print(await demo())

        # 提醒：功能极强，建议，账号只给可信用户，最好只在docker中部署
        config = RpcClient('ksrpc.config', conn)
        print(await config.USER_CREDENTIALS())

        sys = RpcClient('sys', conn)
        print(await sys.path.insert(0, "/kan"))
        print(await sys.path())


asyncio.run(async_main())
