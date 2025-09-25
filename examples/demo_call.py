"""
常见的几种调用方法
"""
import asyncio

from examples.config import USERNAME, PASSWORD, URL_HTTP, URL_WS  # noqa
from ksrpc.client import RpcProxy, rpc_iterator
from ksrpc.connections.http import HttpConnection


async def async_main():
    async with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        server = RpcProxy('ksrpc.server', conn)
        print(await server.demo.test())  # ksrpc.server.demo.test()
        print(await server())  # ksrpc.server
        print(await server.__file__())  # ksrpc.server.__file__

        server = RpcProxy('ksrpc.server', conn)
        print(await server.demo.CLASS.D.C.__getitem__(2))  # ksrpc.server.demo.CLASS.D.C[2]
        print(await server.demo.CLASS.D.C[2])  # ksrpc.server.demo.CLASS.D.C[2]

        # 提醒：账号只给可信用户，最好只在docker中部署
        config = RpcProxy('ksrpc.config', conn)
        print(await config.USER_CREDENTIALS())  # ksrpc.config.USER_CREDENTIALS

        sys = RpcProxy('sys', conn)
        print(await sys.path.insert(0, "/kan"))  # sys.path.insert(0, "/kan")
        print(await sys.path())  # sys.path
        print(await sys.modules.keys())  # sys.modules.keys()

        # 提醒：账号只给可信用户，最好只在docker中部署
        os = RpcProxy("os", conn)
        await os.system('calc')  # os.system('calc') # 打开Windows服务器上的计算器

        builtins = RpcProxy('builtins', conn)
        print(await builtins.globals())
        print(await builtins.locals())
        await builtins.eval("__import__('os').system('calc')")  # 单行。不支持import
        await builtins.exec("import os;os.system('calc')")  # 多行。支持import
        await builtins.exec("""
def greet(name):
    return f"Hello, {name}!"

# 一定到存到globals才能给下一个函数使用。本地开发不需这一步
globals()["greet"] = greet
        """)
        print(await builtins.eval("greet('World')"))  # 调用上一步保存在globals中的方法

        math = RpcProxy('math', conn)
        print(await math.pi())  # math.pi
        print(await math.pi.__round__(4))  # round(math.pi, 4)
        # print(await math.__getattr__('__call__')())  # math()  # 非法，但服务端报错与本地报错一致

        demo = RpcProxy('ksrpc.server.demo', conn)
        print(await demo.create_1d_array.__doc__())  # ksrpc.server.demo.create_1d_array.__doc__
        print(await demo.__doc__.__len__())  # len(ksrpc.server.demo.__doc__)
        print(await demo.p.__format__("p"))  # format(ksrpc.server.demo.p, "p")
        print(await demo.p.__format__.__func__())  # ksrpc.server.demo.p.__format__.__func__
        print(await demo.p.__format__.__func__.__name__())  # ksrpc.server.demo.p.__format__.__func__.__name__

        gen = await demo.sync_counter()  # gen = sync_counter()
        # 为何要两层
        print(await gen.__next__()())  # print(next(gen))
        print(await gen.__next__()())  # print(next(gen))

        demo = RpcProxy('ksrpc.server.demo', conn, reraise=True)

        async for it in rpc_iterator(demo.async_counter()):
            print(it)

        async for it in rpc_iterator(demo.sync_counter()):
            print(it)

        # 注意：如果语句过于复杂，建议在服务器上放一个文件，直接调用模块中封装好的函数。
        # 如果服务器放文件不容易，可以用exec+eval


asyncio.run(async_main())
