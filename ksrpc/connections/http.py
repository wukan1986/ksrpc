import asyncio

import aiohttp

from ksrpc.connections import BaseConnection
from ksrpc.serializer.pkl_gzip import deserialize, serialize


async def process_response(r):
    """处理HTTP响应。根据不同的响应分别处理

    Parameters
    ----------
    r: Response

    Returns
    -------
    object
    json
    csv

    """
    if r.status != 200:
        raise Exception(f'{r.status}, {await r.text()}')
    data = deserialize(await r.content.read())
    if data['status'] == 200:
        return data['data']
    return data


class HttpConnection(BaseConnection):
    """HTTP请求响应模式
    1. 比WebSocket协议开销较高，延迟较高
    2. 一个请求一个连接。并发时会自动建立多个连接
    """

    def __init__(self, url, username=None, password=None):
        super().__init__(url)
        self._client = None
        self._lock = asyncio.Lock()
        self._timeout = aiohttp.ClientTimeout(total=60)
        if username and password:
            self._auth = aiohttp.BasicAuth(login=username, password=password, encoding="utf-8")
        else:
            self._auth = None

    async def __aenter__(self):
        """异步async with"""
        return self

    async def __aexit__(self, exc_type=None, exc_val=None, exc_tb=None):
        """异步async with"""
        async with self._lock:
            if self._client:
                await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def connect(self):
        async with self._lock:
            if self._client is not None:
                return
            self._client = aiohttp.ClientSession(auth=self._auth, timeout=self._timeout)

    async def reset(self):
        async with self._lock:
            if self._client is None:
                return
            await self._client.close()
            self._client = None

    async def call(self, module, name, args, kwargs):
        """调用函数

        Parameters
        ----------
        module: str
            多层模块名
        name:str
            多层模块名+最后一个函数名
        args: tuple
            函数位置参数
        kwargs: dict
            函数命名参数

        """
        await self.connect()

        d = dict(module=module, name=name, args=args, kwargs=kwargs)
        files = dict(file=serialize(d).read())
        r = await self._client.post(self.get_url(), data=files)

        return await process_response(r)
