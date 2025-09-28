import asyncio

from examples.config import USERNAME, PASSWORD, URL_HTTP, URL_WS  # noqa
from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection


async def async_main():
    async with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        demo = RpcClient('ksrpc.server.demo', conn)
        await demo.child_obj.some_method()  # 输出: 这是子类重写后的方法。

        builtins = RpcClient('builtins', conn)

        # Parent.some_method(child_obj)  # 输出: 这是父类的原始方法
        await builtins.exec("""
from ksrpc.server.demo import Parent, child_obj

Parent.some_method(child_obj)
        """)

        # 这种写法本来不正确，现在支持了，可以查询服务器中的属性，方便传参
        await demo.Parent.some_method(demo.child_obj)

    async with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        demo = RpcClient('ksrpc.server.demo', conn, lazy=True)
        await demo.child_obj.some_method().collect_async()  # 输出: 这是子类重写后的方法。

        builtins = RpcClient('builtins', conn, lazy=True)

        # Parent.some_method(child_obj)  # 输出: 这是父类的原始方法
        await builtins.exec("""
from ksrpc.server.demo import Parent, child_obj

Parent.some_method(child_obj)
        """).collect_async()

        # 这种写法本来不正确，现在支持了，可以查询服务器中的属性，方便传参
        await demo.Parent.some_method(demo.child_obj).collect_async()


asyncio.run(async_main())
