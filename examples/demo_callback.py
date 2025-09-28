"""
主要演示以下内容
1. 在服务器上运行客户端的函数。如：sorted，reduce
2. 在客户端运行返回的函数。如：map，filter
3. 更通用的回调函数。（暂不支持）
"""
import asyncio

from examples.config import USERNAME, PASSWORD, URL_HTTP, URL_WS  # noqa
from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection


async def async_main():
    async with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        numbers = [1, 2, 3, 4, 5]
        fruits = ['apple', 'banana', 'cherry', 'date', 'elderberry']

        builtins = RpcClient('builtins', conn)

        def f(x):
            print("这是在本地运行的函数 f")
            return x ** 3

        def is_even(x):
            print("这是在本地运行的函数 is_even")
            return x % 2 == 0

        def length(obj):
            print("这是在服务端运行的函数 length")
            return len(obj)

        print(list(await builtins.map(f, numbers)))  # 返回迭代器的都是延迟计算
        print(list(await builtins.filter(is_even, numbers)))  # 延迟计算都是在本地计算
        print(await builtins.sorted(fruits, key=length))  # 返回普通结果的都是在服务器计算

        functools = RpcClient('functools', conn, lazy=True)

        print(await functools.reduce(
            lambda x, y: print("这是在服务端运行的函数 lambda") or (x * y),
            numbers
        ).collect_async())  # 支持lambda表达式


asyncio.run(async_main())
