import nest_asyncio

from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection  # noqa
from ksrpc.connections.websocket import WebSocketConnection  # noqa

URL = 'http://100.100.100.100:7001/api/v1'
URL = 'http://frp.freefrp.net:7001/api/v1'
URL = 'http://us.afrp.net:7001/api/v1'

USERNAME = 'admin'
PASSWORD = 'password123'

# 必用，否则同步模式只能调用第一次，第二次会报 RuntimeError: Event loop is closed
nest_asyncio.apply()


def async_main():
    with HttpConnection(URL, username=USERNAME, password=PASSWORD) as conn:
        api = RpcClient('jqresearch.api', conn, to_sync=True)
        output = api.generate_stub()
        print(output)
        print(api.get_price(security='000001.XSHE'))

        # 需要先上传jqresearch_query.py
        query = RpcClient('jqresearch_query', conn, lazy=True, to_sync=True)
        output = query.generate_stub().collect()
        print(output)
        print(query.get_fundamentals_valuation(date='2025-09-26').collect())


async_main()
