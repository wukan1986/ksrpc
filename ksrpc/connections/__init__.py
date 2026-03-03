import aiohttp


class BaseConnection:
    def __init__(self, url: str, username=None, password=None, connector=None):
        self._url = url
        self._connector = connector
        if username and password:
            self._auth = aiohttp.BasicAuth(login=username, password=password, encoding="utf-8")
        else:
            self._auth = None

    async def reset(self):
        ...

    async def call(self, module, calls, ref_id):
        ...


class SmartConnection:
    def __new__(cls, url: str, *args, **kwargs):
        """根据协议，智能选择连接类型"""
        protocol = url.split("://")[0]

        if protocol.startswith(("ws", "wss")):
            from ksrpc.connections.websocket import WebSocketConnection
            return WebSocketConnection(url, *args, **kwargs)
        elif protocol.startswith(("http", "https")):
            from ksrpc.connections.http import HttpConnection
            return HttpConnection(url, *args, **kwargs)
        else:
            # TODO 无法识别的也先放这
            from ksrpc.connections.http import HttpConnection
            return HttpConnection(url, *args, **kwargs)
