import nest_asyncio

from examples.config import USERNAME, PASSWORD, URL_HTTP, URL_WS  # noqa
from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection  # noqa
from ksrpc.connections.websocket import WebSocketConnection  # noqa

# 必用，否则同步模式只能调用第一次，第二次会报 RuntimeError: Event loop is closed
nest_asyncio.apply()


def sync_main():
    with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        demo = RpcClient('ksrpc.server.demo', conn, to_sync=True)  # to_sync参数要设置
        print(demo.test())
        print(demo.test())

    with WebSocketConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        demo = RpcClient('ksrpc.server.demo', conn, to_sync=True)  # to_sync参数要设置
        print(demo.test())
        print(demo.test())

    conn = HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD)
    demo = RpcClient('ksrpc.server.demo', conn, to_sync=True)
    print(demo.test())
    print(demo.test())

    conn = WebSocketConnection(URL_HTTP, username=USERNAME, password=PASSWORD)
    demo = RpcClient('ksrpc.server.demo', conn, to_sync=True)
    print(demo.test())
    print(demo.test())




sync_main()
