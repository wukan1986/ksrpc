import aiohttp
from aiohttp import web

from ksrpc.connections import BaseConnection
from ksrpc.serializer.pkl_gzip import serialize, deserialize


def process_response(data):
    if data['status'] == 200:
        return data['data']
    return data


class WebSocketConnection(BaseConnection):
    def __init__(self, url: str, username=None, password=None):
        self._url = url
        self._auth = aiohttp.BasicAuth(login=username, password=password, encoding='utf-8')
        self._timeout = aiohttp.ClientTimeout(total=60)
        self._session = None
        self._ws = None

    async def __aenter__(self):
        """异步async with"""
        return self

    async def __aexit__(self, exc_type=None, exc_value=None, traceback=None):
        """异步async with"""
        if self._session:
            await self._session.__aexit__(exc_type, exc_value, traceback)
        if self._ws:
            await self._ws.__aexit__(exc_type, exc_value, traceback)

    async def connect(self):
        if self._session is not None:
            return
        self._session = aiohttp.ClientSession(auth=self._auth, timeout=self._timeout)
        self._ws = await self._session.ws_connect(self._url).__aenter__()

    async def reset(self):
        if self._session is None:
            return
        await self._session.close()
        self._session = None
        self._ws = None

    async def call(self, module, methods, args, kwargs):
        await self.connect()

        d = dict(module=module, methods=methods, args=args, kwargs=kwargs)

        b = serialize(d).read()
        await self._ws.send_bytes(b)
        async for msg in self._ws:
            if msg.type is web.WSMsgType.BINARY:
                return process_response(deserialize(msg.data))
            elif msg.type == web.WSMsgType.ERROR:
                print('ws connection closed with exception %s' % self._ws.exception())
            elif msg.type is web.WSMsgType.CLOSE:
                break

        return None
