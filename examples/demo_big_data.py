import asyncio
import socket

import aiohttp

from examples.config import USERNAME, PASSWORD, URL  # noqa
from ksrpc.client import RpcClient
from ksrpc.connections import SmartConnection  # noqa
from ksrpc.connections.http import HttpConnection  # noqa
from ksrpc.connections.websocket import WebSocketConnection  # noqa


async def async_main():
    # 本地创建大文件
    from ksrpc.server.demo import create_1d_array
    a = create_1d_array(10)
    print(a)

    # !!! 这个功能不要轻易在云服务器上测试过大文件，大文件只在本地测试即可
    connector = aiohttp.TCPConnector(family=socket.AF_INET)
    async with SmartConnection(URL, username=USERNAME, password=PASSWORD, connector=connector) as conn:
        demo = RpcClient('ksrpc.server.demo', conn)
        ret = await demo.create_1d_array(target_mb=1)
        print(ret)

    # 观察HTTP大文件上传与下载是否正常
    connector = aiohttp.TCPConnector(family=socket.AF_INET)
    proxy = "http://127.0.0.1:10808"
    proxy_auth = aiohttp.BasicAuth('user', 'pass')
    async with HttpConnection(URL, username=USERNAME, password=PASSWORD) as conn:
        demo = RpcClient('ksrpc.server.demo', conn)
        ret = await demo.add(a, 1)
        print(ret)

    # 观察WebSocket大文件上传与下载是否正常
    async with WebSocketConnection(URL, username=USERNAME, password=PASSWORD) as conn:
        demo = RpcClient('ksrpc.server.demo', conn, lazy=True)
        ret = await demo.add(a, 2).collect()
        print(ret)


asyncio.run(async_main())
