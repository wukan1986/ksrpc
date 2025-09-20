"""
动态URL

请与config.py中的check_url_path配合使用
"""
import asyncio
import time

from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection


class ChoiceURL:
    url = 'http://127.0.0.1:8080/api/{}'

    def __call__(self, *args, **kwargs):
        import random
        _url = self.url.format(random.choice(['file', 'test']))
        print(_url)
        return _url


class TimeURL:
    url = 'http://127.0.0.1:8080/api/{}'

    def __call__(self, *args, **kwargs):
        import time
        _url = self.url.format(int(time.time()))
        print(_url)
        return _url


async def async_main():
    async with HttpConnection(ChoiceURL(), username="admin", password="password123") as conn:
        demo = RpcClient('ksrpc.server.demo', conn)
        print(await demo.__file__())
        time.sleep(5)
        print(await demo.__file__())


asyncio.run(async_main())
