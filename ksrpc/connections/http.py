import asyncio
import os
import sys
import time
import zlib
from datetime import datetime

import aiohttp
import dill as pickle

from ksrpc.connections import BaseConnection
from ksrpc.utils.async_ import async_to_sync
from ksrpc.utils.chunks import data_sender, CHUNK_BORDER_BYTES, ZLIB_COMPRESS_LEVEL  # noqa
from ksrpc.utils.misc import format_number
from ksrpc.utils.tqdm import update_progress, muted_print

# 通过环境变量PRINT=0可以屏蔽打印下载进度条
_print = print if os.getenv("PRINT", "1") == '1' else muted_print


async def process_response(response):
    """处理HTTP响应。根据不同的响应分别处理"""
    if response.status != 200:
        raise Exception(f'{response.status}, {await response.text()}')

    file = sys.stderr
    # for resp in response.history:
    #     _print(f"{datetime.now()} {resp.status} {resp.method} {resp.url} {resp.headers["Location"]}", file=file)

    t1 = time.perf_counter()
    _print(f'{datetime.now()} 接收数据: [', end='', file=file)
    buffer = bytearray()
    buf = bytearray()
    i = -1
    size = 0
    async for chunk, end_of_http_chunk in response.content.iter_chunks():
        buf.extend(chunk)
        if end_of_http_chunk:
            bs = buf.split(CHUNK_BORDER_BYTES)
            # 没有出现分隔符，直接返回
            if len(bs) == 1:
                continue

            # 出现了分隔符
            for j, b in enumerate(bs):
                if j == len(bs) - 1:
                    buf.clear()
                    buf.extend(b)
                    continue

                size += len(b)
                buffer.extend(zlib.decompress(b))

            i += 1
            update_progress(i, _print, file=file)
    t2 = time.perf_counter()
    _print(f'] 解压完成 ({format_number(size)}B/{format_number(len(buffer))}B) {t2 - t1:.2f}s {format_number(size / (t2 - t1))}B/s', file=file)
    rsp = pickle.loads(buffer)
    buffer.clear()
    return rsp


class HttpConnection(BaseConnection):
    """HTTP请求响应模式
    1. 比WebSocket协议开销较高，延迟较高
    2. 一个请求一个连接。并发时会自动建立多个连接
    """

    def __init__(self, url: str, username=None, password=None, connector=None, proxy=None, proxy_auth=None):
        """可以使用http://和https://"""
        super().__init__(url, username, password, connector, proxy, proxy_auth)
        self._client = None
        self._lock = asyncio.Lock()
        self._timeout = aiohttp.ClientTimeout(total=60)

    def __enter__(self):
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        async_to_sync(self.reset)
        if self._client:
            self._client.__exit__(exc_type, exc_val, exc_tb)
            self._client = None

    async def __aenter__(self):
        """异步async with"""
        return self

    async def __aexit__(self, exc_type=None, exc_val=None, exc_tb=None):
        """异步async with"""
        await self.reset()
        async with self._lock:
            if self._client:
                await self._client.__aexit__(exc_type, exc_val, exc_tb)
                self._client = None

    def __del__(self):
        if self._client and async_to_sync:
            async_to_sync(self._client.close)
        self._client = None

    async def connect(self):
        async with self._lock:
            if self._client is None:
                self._client = aiohttp.ClientSession(auth=self._auth, timeout=self._timeout,
                                                     connector=self._connector,
                                                     proxy=self._proxy, proxy_auth=self._proxy_auth)

    async def reset(self):
        async with self._lock:
            if self._client:
                await self._client.close()
                self._client = None

    def response_update_url(self, response, key):
        if response.status == 200:
            url = str(response.url).rstrip(key)
            self.data.set("url", url)
        else:
            self.data.set("url", None)
        file = sys.stderr
        for resp in response.history:
            _print(f"{datetime.now()} {resp.status} {resp.method} {resp.url} {resp.headers["Location"]}", file=file)

    async def call(self, module, calls, ref_id):
        """调用函数

        Parameters
        ----------
        module: str
            多层模块名
        calls: list
            调用列表
        ref_id

        """
        await self.connect()

        d = dict(module=module, calls=calls, ref_id=ref_id)

        data = pickle.dumps(d)
        headers = {"X-Timestamp": str(time.time())}

        url = self.data.get("url")
        # 小数据包，重定向也没关系,传整体
        if url is None and len(data) < 1024 * 128:
            url = self._url.rstrip('/')
            response = await self._client.post(
                f"{url}/http",
                # 一次性压缩，在大数据时耗时长
                data=zlib.compress(data, ZLIB_COMPRESS_LEVEL),
                headers=headers,
            )
            self.response_update_url(response, "/http")
            return await process_response(response)

        # 大数据包，为防止数据被传两份，所以先获取重定向地址
        if url is None:
            url = self._url.rstrip('/')
            response = await self._client.post(f"{url}/redirect", headers=headers)
            self.response_update_url(response, "/redirect")

        # 用新地址请求
        response = await self._client.post(
            f"{url}/chunk",
            data=data_sender(data, muted_print),
            headers=headers,
            allow_redirects=False,
        )
        self.response_update_url(response, "/chunk")

        return await process_response(response)
