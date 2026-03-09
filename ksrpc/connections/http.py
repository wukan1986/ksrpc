import asyncio
import sys
import time
import zlib
from datetime import datetime

import aiohttp
import dill as pickle
from aiohttp import web

from ksrpc.config_client import PRINT_PROGRESS, HTTP_ALLOW_REDIRECTS
from ksrpc.connections import BaseConnection, make_headers
from ksrpc.utils.chunks import data_sender, CHUNK_BORDER_BYTES, ZLIB_COMPRESS_LEVEL  # noqa
from ksrpc.utils.misc import format_number
from ksrpc.utils.tqdm import update_progress, muted_print

_print = print if PRINT_PROGRESS > 0 else muted_print


async def process_response(response):
    """处理HTTP响应。根据不同的响应分别处理"""
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
        self._async_to_sync(self.reset)
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
        if self._client:
            self._async_to_sync(self._client.close)
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

    async def response_update_url(self, response, key: str) -> str:
        if response.status in (200, 204):
            url = str(response.url)
            for resp in response.history:
                print(f"{datetime.now()} {resp.status} {resp.method} {resp.url} {resp.headers["Location"]}", file=sys.stderr)
        elif response.status in (301, 302, 303, 307, 308):
            url = response.headers['Location']
            print(f"{datetime.now()} {response.status} {response.method} {response.url} {response.headers["Location"]}", file=sys.stderr)
        else:
            url = None
            raise Exception(f'{response.status}, {await response.text()}, {response.url}')

        if url:
            url = url.rstrip(key)
            self.data.set("url", url)

        return url

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

        url = self.data.get("url")
        # # 小数据包，重定向也没关系,传整体
        # if url is None and len(data) < 1024 * 128:
        #     url = self._url.rstrip('/')
        #     response = await self._client.post(
        #         f"{url}/http",
        #         # 一次性压缩，在大数据时耗时长，307正常，302丢失数据区
        #         data=zlib.compress(data, ZLIB_COMPRESS_LEVEL),
        #         headers=headers,
        #     )
        #     self.response_update_url(response, "/http")
        #     return await process_response(response)

        # 大数据包，为防止数据被传两份，所以先获取重定向地址
        if HTTP_ALLOW_REDIRECTS >= 1:
            if url is None:
                url = self._url.rstrip('/')
                # allow_redirects=True支持多层跳转
                # allow_redirects=False支持一层跳转，速度更快
                response = await self._client.post(f"{url}/generate_204", headers=make_headers(), allow_redirects=HTTP_ALLOW_REDIRECTS >= 2)
                url = await self.response_update_url(response, "/generate_204")
            else:
                # print("获取了历史URL", url)
                pass
        else:
            # 直连
            if url is None:
                url = self._url.rstrip('/')

        # 用新地址请求
        if url:
            response = await self._client.post(
                f"{url}/chunk",
                data=data_sender(data, muted_print),
                headers=make_headers(),
                allow_redirects=False,
            )
            await self.response_update_url(response, "/chunk")

            if response.status in (301, 302, 303, 307, 308):
                if HTTP_ALLOW_REDIRECTS == 0:
                    raise Exception(f'{response.status}, 遇到重定向，请设置环境变量`HTTP_ALLOW_REDIRECTS=1`')
                if HTTP_ALLOW_REDIRECTS == 1:
                    raise Exception(f'{response.status}, 多次重定向，请设置环境变量`HTTP_ALLOW_REDIRECTS=2`')

            return await process_response(response)
        else:
            return web.HTTPForbidden(text=f"url is invalid: {url}")
