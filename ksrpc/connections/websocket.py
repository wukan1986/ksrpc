import asyncio
import pickle
import sys
import zlib

import aiohttp

from ksrpc.connections import BaseConnection
from ksrpc.utils.chunks import send_in_chunks
from ksrpc.utils.tqdm import update_progress, muted_print


def process_response(data):
    if data['status'] == 200:
        return data['data']
    return data


class WebSocketConnection(BaseConnection):
    """WebSocket支持长连接
    1. 比HTTP协议开销较小，延迟较低
    2. 同一连接中，请求不能并行。如需并发要分别建立连接
    """

    def __init__(self, url, username=None, password=None):
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
            self._ws = await self._session.ws_connect(
                self.get_url(),
                # proxy="http://192.168.31.33:9000",
            ).__aenter__()

    async def reset(self):
        async with self._lock:
            if self._ws is None:
                return
            await self._ws.close()
            self._ws = None

    async def call(self, module, name, args, kwargs):
        await self.connect()

        d = dict(module=module, name=name, args=args, kwargs=kwargs)

        # gather时会出错，只能用lock保证一次只能一个请求和响应
        async with self._lock:
            await send_in_chunks(self._ws, pickle.dumps(d), muted_print)

            file = sys.stderr
            print(f'接收数据: [', end='', file=file)
            buffer = bytearray()
            buf = bytearray()
            i = -1
            async for msg in self._ws:
                if msg.type is aiohttp.WSMsgType.BINARY:
                    buf.extend(msg.data)
                elif msg.type == aiohttp.WSMsgType.TEXT:
                    if msg.data == "\r\n":
                        buffer.extend(zlib.decompress(buf))
                        buf.clear()
                        i += 1
                        update_progress(i, print, file=file)
                    elif msg.data == "EOF":
                        print(f'] 接收完成 ({len(buffer)} bytes)', file=file)
                        rsp = pickle.loads(buffer)
                        buffer.clear()
                        return process_response(rsp)
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
