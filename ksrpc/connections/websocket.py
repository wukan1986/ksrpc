import asyncio
import sys
import time
import zlib

import aiohttp
import dill as pickle

from ksrpc.connections import BaseConnection
from ksrpc.utils.async_ import async_to_sync
from ksrpc.utils.chunks import send_in_chunks
from ksrpc.utils.misc import format_number
from ksrpc.utils.tqdm import update_progress, muted_print


class WebSocketConnection(BaseConnection):
    """WebSocket支持长连接
    1. 比HTTP协议开销较小，延迟较低
    2. 同一连接中，请求不能并行。如需并发要分别建立连接
    """

    def __init__(self, url, username=None, password=None):
        super().__init__(url, username, password)
        self._ws = None
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
            async_to_sync(self._client.close)
            self._client = None

    async def connect(self):
        async with self._lock:
            if self._ws is not None:
                return
            if self._client is None:
                self._client = aiohttp.ClientSession(auth=self._auth, timeout=self._timeout)
            self._ws = await self._client.ws_connect(
                self._url.format(time=time.time()),
                # proxy="http://192.168.31.33:9000",
            ).__aenter__()

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

            t1 = time.perf_counter()
            file = sys.stderr
            print(f'接收数据: [', end='', file=file)
            buffer = bytearray()
            buf = bytearray()
            i = -1
            size = 0
            async for msg in self._ws:
                if msg.type is aiohttp.WSMsgType.BINARY:
                    buf.extend(msg.data)
                elif msg.type == aiohttp.WSMsgType.TEXT:
                    if msg.data == "\r\n":
                        size += len(buf)
                        buffer.extend(zlib.decompress(buf))
                        buf.clear()
                        i += 1
                        update_progress(i, print, file=file)
                    elif msg.data == "EOF":
                        t2 = time.perf_counter()
                        print(f'] 解压完成 ({format_number(size)}B/{format_number(len(buffer))}B) {t2 - t1:.2f}s {format_number(size / (t2 - t1))}B/s', file=file)
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
