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
import asyncio
from datetime import datetime
from urllib.parse import urlparse

from loguru import logger
from revolving_asyncio import to_sync
from websockets import __version__ as websockets_version

from ..model import Format, RspModel
from ..serializer.json_ import dict_to_json, json_to_dict, dict_to_obj
from ..serializer.pkl_gzip import serialize, deserialize
from ..utils.check_ import check_methods
from ..utils.notebook import clear_output

is_old = int(websockets_version.split('.')[0]) < 13

# 二进制拆包
BYTES_PER_SEND = 1024 * 32


def process_response_dict(data):
    # data = deserialize(r)
    if data['status'] == 200:
        return data['data']
    return data


def process_response_json(r):
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
        # 默认是2**20，只有1MB，扩充一下成8MB
        if is_old:
            self._client = connect(self._url, extra_headers=headers, max_size=2 ** 23)
        else:
            self._client = connect(self._url, additional_headers=headers, max_size=2 ** 23)

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
                   async_remote=True,
                   timeout=30):
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
            b = serialize(d).read()
            bl = len(b)
            await self._ws.send(serialize(bl).read())
            for i in range(0, len(b), BYTES_PER_SEND):
                await self._ws.send(b[i:i + BYTES_PER_SEND])
        else:
            # json格式
            await self._ws.send(dict_to_json(d))

        # 这里收到的数据是否需要解析一下，如果是二进制的，需要特别处理
        rsp = await asyncio.wait_for(self._ws.recv(), timeout)
        if isinstance(rsp, bytes):
            # 二进制，反序列化后是字典
            bl = deserialize(rsp)
            rsp = b''
            while len(rsp) < bl:
                rsp += await asyncio.wait_for(self._ws.recv(), timeout)
            return process_response_dict(deserialize(rsp))
        else:
            return process_response_json(rsp)

    async def reverse(self, recv_timeout=True, clear_cnt=5):
        """反弹RPC的被控端"""
        from ..caller import call

        recv_count = 0
        _clear_cnt = 0
        while True:
            if recv_timeout:
                # 对第一个数据包长度添加超时机制
                timeout_count = 0
                while True:
                    try:
                        # 等15秒
                        req = await asyncio.wait_for(self._ws.recv(), 30)
                        timeout_count = 0
                        break
                    except asyncio.TimeoutError:
                        timeout_count += 1
                        # print('接收超时')
                        if timeout_count >= 2:
                            # 约60秒
                            # print('接收超时断开')
                            return recv_count
            else:
                # 一直等待，无超时
                req = await self._ws.recv()

            recv_count += 1
            bl = deserialize(req)
            req = b''
            while len(req) < bl:
                req += await self._ws.recv()
            req = deserialize(req)
            # 可能显示太多，需要裁剪一些
            logger.info(repr(req)[:200])
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
                # 每个连上去的都分别使用了自己的用户名，这里不需要用户名即可操作
                user = 'reverse'
                key, buf, data = await call(user, **req)
            except Exception as e:
                # 主要是处理
                key = type(e).__name__
                # 这里没有缓存，因为这个错误是服务器内部检查
                data = RspModel(status=401,  # status.HTTP_401_UNAUTHORIZED,
                                datetime=datetime.now().isoformat(),
                                func=func, args=req['args'], kwargs=req['kwargs'])
                data.type = type(e).__name__
                data.data = repr(e)
                data = data.model_dump() if hasattr(data, 'model_dump') else data.dict()
                buf = serialize(data).read()

            # 释放内存
            del data
            del req
            # 将这里分成两种处理方法
            bl = len(buf)
            print(f'需发送字节数:{bl} ', end='')
            await self._ws.send(serialize(bl).read())
            for i in range(0, len(buf), BYTES_PER_SEND):
                print('>', end='')
                await self._ws.send(buf[i:i + BYTES_PER_SEND])
                print('\b=', end='')
            print(' 发送完成')
            # 释放内存
            del buf
            _clear_cnt += 1
            if _clear_cnt >= clear_cnt:
                _clear_cnt = 0
                clear_output()
