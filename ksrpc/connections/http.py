import asyncio
import pickle
import sys
import zlib

import aiohttp

from ksrpc.connections import BaseConnection
from ksrpc.utils.chunks import data_sender
from ksrpc.utils.tqdm import update_progress, muted_print


async def process_response(response):
    """处理HTTP响应。根据不同的响应分别处理

    Parameters
    ----------
    response: Response

    Returns
    -------
    object
    json
    csv

    """
    if response.status != 200:
        raise Exception(f'{response.status}, {await response.text()}')

    file = sys.stderr
    print(f'接收数据: [', end='', file=file)
    buffer = bytearray()
    buf = bytearray()
    i = -1
    size = 0
    async for chunk, end_of_http_chunk in response.content.iter_chunks():
        buf.extend(chunk)
        if end_of_http_chunk:
            if len(buf) == 0:
                continue
            size += len(buf)
            buffer.extend(zlib.decompress(buf))
            buf.clear()
            i += 1
            update_progress(i, print, file=file)

    print(f'] 解压完成 ({size:,}/{len(buffer):,} bytes)', file=file)
    rsp = pickle.loads(buffer)
    buffer.clear()
    if rsp['status'] == 200:
        return rsp['data']
    return rsp


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

        data = pickle.dumps(d)
        headers = {}

        response = await self._client.post(
            self.get_url(),
            data=data_sender(data, muted_print),
            headers=headers,
            # proxy="http://192.168.31.33:9000",
        )

        return await process_response(response)
