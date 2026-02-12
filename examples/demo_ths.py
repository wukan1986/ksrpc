import asyncio

from examples.config import USERNAME, PASSWORD, URL_HTTP, URL_WS  # noqa
from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection  # noqa
from ksrpc.connections.websocket import WebSocketConnection  # noqa

URL_HTTP = 'http://127.0.0.1:8080/api/v1/{time}'

USERNAME = 'admin'
PASSWORD = 'password123'


async def async_main():
    # 观察HTTP大文件上传与下载是否正常
    async with HttpConnection(URL_HTTP, username=USERNAME, password=PASSWORD) as conn:
        research_api = RpcClient('mgquant_mod_stock.research_api', conn)
        ret = await research_api.query_iwencai("近10日的区间主力资金流向>5000万元，市值>1000亿，日成交额>30亿")
        print(ret)


asyncio.run(async_main())
