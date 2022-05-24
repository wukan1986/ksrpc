#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author     :wukan
# @License    :(C) Copyright 2022, wukan
# @Date       :2022-05-16

"""
使用wesockets实现的客户端
1. 默认提交pickle格式，返回也是pickle格式
2. 原接口是异步版，必须使用async with，封装成了同步版with
3. 为了使用方便，还提供了不需with的版本，可直接调用

"""

from ..model import ReqFmt, Format
from ..serializer.json_ import dict_to_json, json_to_dict, dict_to_obj
from ..serializer.pkl_gzip import serialize, deserialize
from ..utils.async_ import to_sync


def process_response(r):
    """处理响应。根据不同的响应分别处理

    Parameters
    ----------
    r: Response

    Returns
    -------
    object
    json
    csv

    """
    if isinstance(r, bytes):
        # 二进制，反序列化后是字典
        data = deserialize(r)
        if data['status'] == 200:
            return data['data']
        return data
    else:
        # json字符串转成字字典
        data = json_to_dict(r)
        # 特殊类型先还原
        if data.get('type', None) in ('DataFrame', 'Series', 'ndarray'):
            data['data'] = dict_to_obj(data['data'])
        # 成功响应直接返回数据区
        if data['status'] == 200:
            return data['data']
        return data


class WebSocketConnection:
    def __init__(self, url, token=None):
        self._url = url
        self._token = token
        self._with = False  # 记录是否用了with
        self._is_json = False  # 默认通讯格式设置，默认使用二进制通讯，减少类型等信息丢失

    async def __aenter__(self):
        """异步async with"""
        from websockets import connect

        headers = None if self._token is None else {"Authorization": f"Bearer {self._token}"}

        if self._is_json:
            self._client = connect(self._url + f'/json', extra_headers=headers)
        else:
            # 浏览器不支持headers，但写在query区又不安全 ?token={self._token}
            self._client = connect(self._url + f'/bytes', extra_headers=headers)

        self._ws = await self._client.__aenter__()
        self._with = True
        return self

    async def __aexit__(self, exc_type=None, exc_value=None, traceback=None):
        """异步async with"""
        await self._client.__aexit__(exc_type, exc_value, traceback)

    def __enter__(self):
        """同步with

        !!! 目前测试发现只能异步，同步无法使用
        """
        to_sync(self.__aenter__)()
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        """同步with"""
        to_sync(self.__aexit__)()

    async def call(self, func, args, kwargs,
                   fmt: Format = Format.PKL_GZIP,
                   cache_get: bool = True, cache_expire: int = 3600):
        # 还没有执行过with就内部主动执行一次
        if not self._with:
            await self.__aenter__()

        d = dict(func=func, args=args, kwargs=kwargs,
                 cache_get=cache_get, cache_expire=cache_expire)

        fmt = Format.JSON if self._is_json else Format.PKL_GZIP

        if fmt == Format.PKL_GZIP:
            # 二进制格式
            buf = serialize(d).read()
            await self._ws.send(buf)
            rsp = await self._ws.recv()
            return process_response(rsp)
        else:
            # json格式
            await self._ws.send(dict_to_json(d))
            rsp = await self._ws.recv()
            return process_response(rsp)
