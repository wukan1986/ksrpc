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

import pandas as pd

from ..model import ReqFmt, RspFmt
from ..serializer.json_ import dict_to_obj
from ..serializer.pkl_gzip import deserialize, serialize
from ..utils.async_ import to_sync


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


class RequestsConnection:
    """使用requests实现的客户端连接"""

    # 超时，请求超求和响应超时，秒
    timeout = (5, 30)

    def __init__(self, url, token=None):
        """

        Parameters
        ----------
        url

        """
        import requests

        self._url = url
        self._token = token
        self._session = requests.Session()

    async def __aenter__(self):
        """异步async with"""
        return self

    async def __aexit__(self, exc_type=None, exc_value=None, traceback=None):
        """异步async with"""
        pass

    def __enter__(self):
        """同步with"""
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        """同步with"""
        pass

    def call(self, func, args, kwargs,
             req_fmt: ReqFmt = ReqFmt.PKL_GZIP, rsp_fmt: RspFmt = RspFmt.PKL_GZIP,
             cache_get: bool = True, cache_expire: int = 3600):
        """调用函数

        Parameters
        ----------
        func: str
            函数全名
        args: tuple
            函数位置参数
        kwargs: dict
            函数命名参数
        req_fmt: ReqFmt
            明示请求格式
        rsp_fmt: RspFmt
            指定响应格式
        cache_get: bool
            是否优先从缓存中获取
        cache_expire: int
            指定缓存超时。超时此时间将过期，指定0表示不进行缓存

        """
        params = dict(func=func, rsp_fmt=rsp_fmt, cache_get=cache_get, cache_expire=cache_expire)
        data = {'args': args, 'kwargs': kwargs}
        headers = None if self._token is None else {"Authorization": f"Bearer {self._token}"}

        if req_fmt == ReqFmt.PKL_GZIP:
            files = {"file": serialize(data).read()}
            r = self._session.post(self._url + '/file',
                                   headers=headers, params=params, timeout=self.timeout, files=files)
        elif req_fmt == ReqFmt.JSON:
            r = self._session.post(self._url + '/post',
                                   headers=headers, params=params, timeout=self.timeout, json=data)

        return process_response(r)


class HttpxConnection:
    """使用httpx实现的客户端连接支持同步和异步"""
    # 超时，请求超求和响应超时，秒
    timeout = (5, 30)

    def __init__(self, url, token=None):
        import httpx

        self._url = url
        self._token = token
        self._client = httpx.AsyncClient()

    async def __aenter__(self):
        """异步async with"""
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type=None, exc_value=None, traceback=None):
        """异步async with"""
        await self._client.__aexit__(exc_type, exc_value, traceback)

    def __enter__(self):
        """同步with"""
        to_sync(self._client.__aenter__)()
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        """同步with"""
        to_sync(self._client.__aexit__)()

    async def call(self, func, args, kwargs,
                   req_fmt: ReqFmt = ReqFmt.PKL_GZIP, rsp_fmt: RspFmt = RspFmt.PKL_GZIP,
                   cache_get: bool = True, cache_expire: int = 3600):
        """调用函数

        Parameters
        ----------
        func: str
            函数全名
        args: tuple
            函数位置参数
        kwargs: dict
            函数命名参数
        req_fmt: ReqFmt
            明示请求格式
        rsp_fmt: RspFmt
            指定响应格式
        cache_get: bool
            是否优先从缓存中获取
        cache_expire: int
            指定缓存超时。超时此时间将过期，指定0表示不进行缓存

        """
        # httpx解析枚举有问题，只能提前转成value，而requests没有此问题
        params = dict(func=func, rsp_fmt=rsp_fmt.value, cache_get=cache_get, cache_expire=cache_expire)
        data = {'args': args, 'kwargs': kwargs}
        headers = None if self._token is None else {"Authorization": f"Bearer {self._token}"}

        if req_fmt == ReqFmt.PKL_GZIP:
            files = {"file": serialize(data).read()}
            r = await self._client.post(self._url + '/file',
                                        headers=headers, params=params, timeout=self.timeout, files=files)
        elif req_fmt == ReqFmt.JSON:
            r = await self._client.post(self._url + '/post',
                                        headers=headers, params=params, timeout=self.timeout, json=data)

        return process_response(r)
