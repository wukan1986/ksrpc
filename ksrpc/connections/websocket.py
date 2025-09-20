import asyncio

import aiohttp
from aiohttp import web

from ksrpc.connections import BaseConnection
from ksrpc.serializer.pkl_gzip import serialize, deserialize


def process_response(data):
    if data['status'] == 200:
        return data['data']
    return data


class WebSocketConnection(BaseConnection):
    """WebSocket支持长连接
    1. 比HTTP协议开销较小，延迟较低
    2. 同一连接中，请求不能并行。如需并发要分别建立连接
    """

    def __init__(self, url: str, username=None, password=None):
        super().__init__(url)
        self._ws = None
        self._lock = asyncio.Lock()
        self._timeout = aiohttp.ClientTimeout(total=60)
        if username and password:
            self._auth = aiohttp.BasicAuth(login=username, password=password, encoding="utf-8")
        else:
            self._auth = None
        self._session = aiohttp.ClientSession(auth=self._auth, timeout=self._timeout)

    async def __aenter__(self):
        """异步async with"""
        return self

    async def __aexit__(self, exc_type=None, exc_value=None, traceback=None):
        """异步async with"""
        async with self._lock:
            if self._ws:
                await self._ws.__aexit__(exc_type, exc_value, traceback)
            if self._session:
                await self._session.__aexit__(exc_type, exc_value, traceback)

    async def connect(self):
        async with self._lock:
            if self._ws is not None:
                return
            self._ws = await self._session.ws_connect(self.get_url()).__aenter__()

    async def reset(self):
        async with self._lock:
            if self._ws is None:
                return
            await self._ws.close()
            self._ws = None

    async def call(self, module, name, args, kwargs):
        await self.connect()

        d = dict(module=module, name=name, args=args, kwargs=kwargs)
        b = serialize(d).read()

        async with self._lock:
            # gather时会出错，只能用lock保证一次只能一个请求和响应
            await self._ws.send_bytes(b)
            async for msg in self._ws:
                if msg.type is web.WSMsgType.BINARY:
                    return process_response(deserialize(msg.data))
                elif msg.type == web.WSMsgType.ERROR:
                    print('ws connection closed with exception %s' % self._ws.exception())
                elif msg.type is web.WSMsgType.CLOSE:
                    break

        return None
