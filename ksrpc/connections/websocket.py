import asyncio
import sys
import time
import zlib
from datetime import datetime

import aiohttp
import dill as pickle

from ksrpc.config_client import PRINT_PROGRESS
from ksrpc.connections import BaseConnection
from ksrpc.utils.chunks import send_in_chunks, CHUNK_BORDER
from ksrpc.utils.misc import format_number
from ksrpc.utils.tqdm import update_progress, muted_print

_print = print if PRINT_PROGRESS > 0 else muted_print


class WebSocketConnection(BaseConnection):
    """WebSocket支持长连接
    1. 比HTTP协议开销较小，延迟较低
    2. 同一连接中，请求不能并行。如需并发要分别建立连接
    """

    def __init__(self, url, username=None, password=None, connector=None, proxy=None, proxy_auth=None):
        """可以使用ws://和wss://，但http://和https://也能兼容"""
        super().__init__(url, username, password, connector, proxy, proxy_auth)
        self._ws = None
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

    async def __aexit__(self, exc_type=None, exc_value=None, traceback=None):
        """异步async with"""
        await self.reset()
        async with self._lock:
            if self._ws:
                await self._ws.__aexit__(exc_type, exc_value, traceback)
                self._ws = None
            if self._client:
                await self._client.__aexit__(exc_type, exc_value, traceback)
                self._client = None

    def __del__(self):
        # 如何知道是async with还是普通创建？
        if self._client:
            self._async_to_sync(self._client.close)
        self._client = None

    def response_update_url(self, response, key: str) -> str:
        if response.status == 101:
            url = str(response.url)
            for resp in response.history:
                print(f"{datetime.now()} {resp.status} {resp.method} {resp.url} {resp.headers["Location"]}", file=sys.stderr)
        else:
            url = None

        if url:
            url = url.rstrip(key)
            self.data.set("url", url)

        return url

    async def connect(self):
        async with self._lock:
            if self._ws is not None:
                return
            if self._client is None:
                self._client = aiohttp.ClientSession(auth=self._auth, timeout=self._timeout,
                                                     connector=self._connector,
                                                     proxy=self._proxy, proxy_auth=self._proxy_auth)

            url = self.data.get("url")
            if url is None:
                url = self._url.rstrip('/')
            else:
                # print("获取了历史URL", url)
                pass

            headers = {"X-Timestamp": str(time.time())}
            self._ws = await self._client.ws_connect(f"{url}/ws", headers=headers).__aenter__()
            self.response_update_url(self._ws._response, "/ws")

    async def reset(self):
        async with self._lock:
            if self._client:
                await self._client.close()
                self._client = None
            if self._ws:
                await self._ws.close()
                self._ws = None

    async def call(self, module, calls, ref_id):
        await self.connect()

        d = dict(module=module, calls=calls, ref_id=ref_id)

        # gather时会出错，只能用lock保证一次只能一个请求和响应
        async with self._lock:
            await send_in_chunks(self._ws, pickle.dumps(d), muted_print)

            file = sys.stderr

            t1 = time.perf_counter()
            _print(f'{datetime.now()} 接收数据: [', end='', file=file)
            buffer = bytearray()
            buf = bytearray()
            i = -1
            size = 0
            async for msg in self._ws:
                if msg.type is aiohttp.WSMsgType.BINARY:
                    buf.extend(msg.data)
                elif msg.type == aiohttp.WSMsgType.TEXT:
                    if msg.data == CHUNK_BORDER:
                        size += len(buf)
                        buffer.extend(zlib.decompress(buf))
                        buf.clear()
                        i += 1
                        update_progress(i, _print, file=file)
                    elif msg.data == "EOF":
                        t2 = time.perf_counter()
                        _print(f'] 解压完成 ({format_number(size)}B/{format_number(len(buffer))}B) {t2 - t1:.2f}s {format_number(size / (t2 - t1))}B/s', file=file)
                        rsp = pickle.loads(buffer)
                        buffer.clear()
                        return rsp
                # elif msg.type is aiohttp.WSMsgType.PING:
                #     await self._ws.pong()
                # elif msg.type is aiohttp.WSMsgType.PONG:
                #     print("Pong received")
                else:
                    if msg.type is aiohttp.WSMsgType.CLOSE:
                        print('Client WebSocket connection close')
                        await self._ws.close()
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print('Client WebSocket connection closed with exception %s' % self._ws.exception())
                    elif msg.type is aiohttp.WSMsgType.CLOSED:
                        print('Client WebSocket connection closed')

                    break

        # TODO 服务端忽然中断，客户端会直接到这一步
        # 这会让ddump开始retry
        raise RuntimeError("End of call")
