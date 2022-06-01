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
from datetime import datetime
from urllib.parse import urlparse

from loguru import logger

from ..caller import call
from ..utils.check_ import check_methods
from ..model import Format, RspModel
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
    def __init__(self, url: str, token=None):
        path = urlparse(url).path
        assert path.endswith(('/json', '/bytes', '/client', '/admin')), 'Python语言优先使用bytes，其它语言使用json'

        if path.endswith('/json'):
            self._fmt = Format.JSON
        else:
            self._fmt = Format.PKL_GZIP

        self._url = url
        self._token = token
        self._with = False  # 记录是否用了with

    async def __aenter__(self):
        """异步async with"""
        from websockets import connect

        headers = None if self._token is None else {"Authorization": f"Bearer {self._token}"}
        self._client = connect(self._url, extra_headers=headers)

        self._ws = await self._client.__aenter__()
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
                   async_remote=True):
        # 还没有执行过with就内部主动执行一次
        if not self._with:
            await self.__aenter__()

        # 如果是JSON格式可以考虑返回CSV
        rsp_fmt = self._fmt

        d = dict(func=func, args=args, kwargs=kwargs,
                 fmt=rsp_fmt.value,
                 cache_get=cache_get, cache_expire=cache_expire, async_remote=async_remote)

        if self._fmt == Format.PKL_GZIP:
            # 二进制格式
            await self._ws.send(serialize(d).read())
        else:
            # json格式
            await self._ws.send(dict_to_json(d))

        rsp = await self._ws.recv()
        return process_response(rsp)

    async def reverse(self):
        """反弹RPC的被控端"""
        while True:
            req = await self._ws.recv()
            req = deserialize(req)
            logger.info(req)
            # 不需要缓存
            req['cache_get'] = False
            req['cache_expire'] = 0
            func = req['func']
            try:
                from ..config import METHODS_ALLOW, METHODS_BLOCK, METHODS_CHECK

                # 反弹RPC权限要进行限制
                if METHODS_CHECK:
                    methods = func.split('.')
                    if not check_methods(METHODS_ALLOW, methods, False):
                        raise Exception(f'Method Not Allowed, {func} not in allowlist')
                    if not check_methods(METHODS_BLOCK, methods, True):
                        raise Exception(f'Method Not Allowed, {func} in blocklist')

                key, buf, data = await call(**req)
            except Exception as e:
                # 主要是处理
                key = type(e).__name__
                # 这里没有缓存，因为这个错误是服务器内部检查
                data = RspModel(status=401,  # status.HTTP_401_UNAUTHORIZED,
                                datetime=datetime.now().isoformat(),
                                func=func, args=req['args'], kwargs=req['args'])
                data.type = type(e).__name__
                data.data = repr(e)
                data = data.dict()
                buf = serialize(data).read()

            await self._ws.send(buf)
