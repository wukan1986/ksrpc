"""
提醒：账号只给可信用户，最好只在docker中部署

注意：如果语句过于复杂，建议在服务器上放一个文件，直接调用文件中封装好的函数。
"""
import asyncio

from examples.config import USERNAME, PASSWORD, URL_HTTP, URL_WS  # noqa
from ksrpc.client import RpcClient, Self
from ksrpc.connections.http import HttpConnection


async def async_main():
    async with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        # 提醒：账号只给可信用户，最好只在docker中部署
        config = RpcClient('ksrpc.config', conn)
        print(await config.USER_CREDENTIALS())  # ksrpc.config.USER_CREDENTIALS

        builtins = RpcClient('builtins', conn)
        ksrpc = await builtins.__import__('ksrpc')
        print(ksrpc.config.USER_CREDENTIALS)  # ksrpc.config.USER_CREDENTIALS

        print(await builtins.globals())
        print(await builtins.locals())

        def length(x):
            print("这是在服务端运行的函数 length。与builtins.exec比，有IDE语法提示")
            import os
            os.system('calc')
            return x

        print(await builtins.sorted([1], key=length))

        os = RpcClient("os", conn)
        await os.system('calc')  # os.system('calc') # 打开Windows服务器上的计算器

        await builtins.eval("__import__('os').system('calc')")  # 单行。不支持import
        await builtins.exec("import os;os.system('calc')")  # 多行。支持import
        await builtins.exec("""
def greet(name):
    print("这是在服务端运行的函数 greet")
    return f"Hello, {name}!"

# 一定要存到globals才能被其他函数调用。本地开发不需这一步
globals()["greet"] = greet
""")
        print(await builtins.eval("greet('World')"))  # 调用上一步保存在globals中的方法

        # 更复杂的写法要开启lazy模式
        builtins = RpcClient('builtins', conn, lazy=True)
        print(await builtins.globals()['__name__'].collect_async())

        # 修改导入库路径
        sys = RpcClient('sys', conn)
        print(await sys.path.insert(0, "/kan"))  # sys.path.insert(0, "/kan")
        print(await sys.path())  # sys.path

        # 通过其他库绕一下，也能取到sys，除非IMPORT_RULES中 "sys": False
        collections = RpcClient('collections', conn, lazy=True)
        print(await collections._sys.path.collect_async())

        # 利用Self查看源代码
        demo = RpcClient('ksrpc.server.demo', conn, lazy=True)
        source = await demo.__file__.open(Self, 'r', encoding='utf-8').read().collect_async()
        print(source)

        # 利用RpcClient远程取属性实现的查看源代码
        builtins = RpcClient('builtins', conn, lazy=True)
        source = await builtins.open(demo.__file__, 'r', encoding='utf-8').read().collect_async()
        print(source)


asyncio.run(async_main())
