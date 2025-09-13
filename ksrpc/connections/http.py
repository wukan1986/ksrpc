#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author     :wukan
# @License    :(C) Copyright 2022, wukan
# @Date       :2022-05-15

"""
HTTP客户端
默认提交pickle格式，返回也是pickle格式

1. RequestsConnection，使用requests实现。原本只支持同步，但此处已经改成支持异步
2. HttpxConnection，使用httpx实现。使用异步，但也可以指定成同步使用

"""
from io import BytesIO
from urllib.parse import urlparse

import pandas as pd
from revolving_asyncio import to_sync

from ..model import Format
from ..serializer.json_ import dict_to_obj
from ..serializer.pkl_gzip import deserialize, serialize


def process_response(r):
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
    if r.status_code != 200:
        raise Exception(f'{r.status_code}, {r.text}')
    content_type = r.headers['content-type']
    if content_type.startswith('application/octet-stream'):
        data = deserialize(r.content)
        if data['status'] == 200:
            return data['data']
        return data
    elif content_type.startswith('application/json'):
        data = r.json()
        if data.get('type', None) in ('DataFrame', 'Series', 'ndarray'):
            return dict_to_obj(data['data'])
        if data['status'] == 200:
            return data['data']
        return data
    elif content_type.startswith('text/plain'):
        # 纯文本，表示返回的CSV格式
        return pd.read_csv(BytesIO(r.content), index_col=0)


class HttpxConnection:
    """使用httpx实现的客户端连接支持同步和异步"""

    def __init__(self, url, token=None, username=None, password=None):
        import httpx

        path = urlparse(url).path
        assert path.endswith(('/get', '/post', '/file')), 'Python语言优先使用file，其它语言使用post'
        if path.endswith('/file'):
            self._fmt = Format.PKL_GZIP
        else:
            self._fmt = Format.JSON

        self._url = url
        self._token = token
        self._with = False
        self._auth = None if username is None else httpx.BasicAuth(username, password)

    async def __aenter__(self):
        """异步async with"""
        import httpx
        self._client = httpx.AsyncClient(auth=self._auth)

        await self._client.__aenter__()
        self._with = True
        return self

    async def __aexit__(self, exc_type=None, exc_value=None, traceback=None):
        """异步async with"""
        await self._client.__aexit__(exc_type, exc_value, traceback)

    def __enter__(self):
        """同步with"""
        to_sync(self.__aenter__)()
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        """同步with"""
        to_sync(self.__aexit__)()

    async def call(self, func, args, kwargs,
                   fmt: Format = Format.PKL_GZIP,
                   cache_get: bool = True, cache_expire: int = 3600,
                   async_remote=True,
                   timeout=30):
        """调用函数

        Parameters
        ----------
        func: str
            函数全名
        args: tuple
            函数位置参数
        kwargs: dict
            函数命名参数
        fmt: Format
            指定响应格式
        cache_get: bool
            是否优先从缓存中获取
        cache_expire: int
            指定缓存超时。超时此时间将过期，指定0表示不进行缓存
        async_remote: bool
            异步方式调用
        timeout: int
            超时时间，单位秒


        """
        if not self._with:
            await self.__aenter__()

        # 如果是JSON格式可以考虑返回CSV
        rsp_fmt = self._fmt

        # httpx解析枚举有问题，只能提前转成value，而requests没有此问题
        params = dict(func=func, fmt=rsp_fmt.value,
                      cache_get=cache_get, cache_expire=cache_expire, async_remote=async_remote)
        data = {'args': args, 'kwargs': kwargs}
        headers = None if self._token is None else {"Authorization": f"Bearer {self._token}"}

        if self._fmt == Format.PKL_GZIP:
            files = {"file": serialize(data).read()}
            r = await self._client.post(self._url, headers=headers, params=params, timeout=timeout, files=files)
        elif self._fmt == Format.JSON:
            r = await self._client.post(self._url, headers=headers, params=params, timeout=timeout, json=data)

        return process_response(r)
