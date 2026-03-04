import aiohttp

from ksrpc.utils.misc import ExpirableProperty


class BaseConnection:
    def __init__(self, url: str, username: str = None, password: str = None, connector=None, proxy=None, proxy_auth=None):
        self._url = url
        self._connector = connector
        self._proxy = proxy
        self._proxy_auth = proxy_auth
        self._auth = aiohttp.BasicAuth(login=username, password=password, encoding="utf-8") if username and password else None
        # 变量超时, 目前缓存的是重定向后的url
        self._expirable = ExpirableProperty(timeout=300)

    @property
    def data(self):
        return self._expirable

    async def reset(self):
        ...

    async def call(self, module, calls, ref_id):
        ...


class SmartConnection:
    def __new__(cls, url: str, username: str = None, password: str = None, connector=None, proxy=None, proxy_auth=None):
        """根据协议，智能选择连接类型"""
        protocol = url.split("://")[0]

        if protocol.startswith(("ws", "wss")):
            from ksrpc.connections.websocket import WebSocketConnection
            return WebSocketConnection(url, username, password, connector, proxy, proxy_auth)
        elif protocol.startswith(("http", "https")):
            from ksrpc.connections.http import HttpConnection
            return HttpConnection(url, username, password, connector, proxy, proxy_auth)
        else:
            # TODO 无法识别的也先放这
            from ksrpc.connections.http import HttpConnection
            return HttpConnection(url, username, password, connector, proxy, proxy_auth)
