import asyncio

from examples.config import USERNAME, PASSWORD, URL_HTTP, URL_WS  # noqa
from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection  # noqa
from ksrpc.connections.websocket import WebSocketConnection  # noqa


async def async_main():
    # 本地创建大文件
    from ksrpc.server.demo import create_1d_array
    a = create_1d_array(10)
    print(a)

    # !!! 这个功能不要轻易在云服务器上测试过大文件，大文件只在本地测试即可

    # 观察HTTP大文件上传与下载是否正常
    async with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        demo = RpcClient('ksrpc.server.demo', conn)
        ret = await demo.add(a, 1)
        print(ret)
    # 观察WebSocket大文件上传与下载是否正常
    async with WebSocketConnection(URL_WS, username=USERNAME, password=PASSWORD) as conn:
        demo = RpcClient('ksrpc.server.demo', conn, lazy=True)
        ret = await demo.add(a, 2).collect()
        print(ret)


asyncio.run(async_main())
