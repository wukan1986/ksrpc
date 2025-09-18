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
        raise Exception(f'{r.status}, {r.text}')
    data = deserialize(await r.content.read())
    if data['status'] == 200:
        return data['data']
    return data


class HttpConnection(BaseConnection):
    """使用aiohttp实现的客户端连接支持同步和异步"""

    def __init__(self, url, username=None, password=None):
        self._url = url
        self._auth = aiohttp.BasicAuth(login=username, password=password, encoding="utf-8")
        self._timeout = aiohttp.ClientTimeout(total=60)
        self._client = None

    async def __aenter__(self):
        """异步async with"""
        return self

    async def __aexit__(self, exc_type=None, exc_val=None, exc_tb=None):
        """异步async with"""
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def connect(self):
        if self._client is not None:
            return
        self._client = aiohttp.ClientSession(auth=self._auth, timeout=self._timeout)

    async def reset(self):
        if self._client is None:
            return
        await self._client.close()
        self._client = None

    async def call(self, module, methods, args, kwargs):
        """调用函数

        Parameters
        ----------
        module: str
            模块名
        methods: str
            函数全名
        args: tuple
            函数位置参数
        kwargs: dict
            函数命名参数

        """
        await self.connect()

        d = dict(module=module, methods=methods, args=args, kwargs=kwargs)
        files = dict(file=serialize(d).read())
        r = await self._client.post(self._url, data=files)

        return await process_response(r)
