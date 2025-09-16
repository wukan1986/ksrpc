#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author     :wukan
# @License    :(C) Copyright 2022, wukan
# @Date       :2022-05-09
"""
调用器
根据指定参数，调用，并返回结果
"""

from datetime import datetime

from loguru import logger
from revolving_asyncio import to_async, to_sync

from .cache import async_cache_get, async_cache_setex
from .caller_simple import make_key
from .config import IP_ALLOW, IP_BLOCK, IP_CHECK, METHODS_CHECK, ENABLE_SERVER
from .serializer.pkl_gzip import serialize
from .utils.check_ import check_methods, check_ip


def before_call(host, user, module, methods):
    """调用前的检查"""
    from .config import (
        METHODS_ALLOW, METHODS_BLOCK,
    )

    if not ENABLE_SERVER:
        raise Exception(f'Service offline')

    if IP_CHECK:
        from IPy import IP
        # 两张清单数据提前处理，加快处理速度
        __IP_ALLOW__ = {IP(k): v for k, v in IP_ALLOW.items()}
        __IP_BLOCK__ = {IP(k): v for k, v in IP_BLOCK.items()}

        host = IP(host)
        if not check_ip(__IP_ALLOW__, host, False):
            raise Exception(f'IP Not Allowed, {host} not in allowlist')
        if not check_ip(__IP_BLOCK__, host, True):
            raise Exception(f'IP Not Allowed, {host} in blocklist')

    if user is None:
        raise Exception(f"Unauthorized")

    methods_list = module.split('.') + methods.split('.')

    if METHODS_CHECK:
        if not check_methods(METHODS_ALLOW, methods_list, False):
            raise Exception(f'Method Not Allowed, {module}::{methods} not in allowlist')
        if not check_methods(METHODS_BLOCK, methods_list, True):
            raise Exception(f'Method Not Allowed, {module}::{methods} in blocklist')


async def call(user, module, methods, args, kwargs, cache_get, cache_expire, async_remote, fmt=None):
    try:
        buf = None
        data = None  # None表示从缓存中取的，需要其它格式时需要转换
        # cache所用的key
        key = make_key(module, methods, args, kwargs)

        if cache_get:
            # 优先取缓存
            buf = await async_cache_get(key)
        if buf is None:
            cache_expire, buf, data = await _call(user, module, methods, args, kwargs, cache_expire, async_remote)

            # 过短的缓存时间没有必要
            if cache_expire >= 30:
                # 就算强行去查询数据，也会想办法存下，再次取时还能从缓存中取
                await async_cache_setex(key, cache_expire, buf)
                logger.info(f'To cache: expire:{cache_expire}\tlen:{len(buf)}\t{key}')
        else:
            logger.info(f'From cache: {module}::{methods}\t{args}\t{kwargs}')

    except Exception as e:
        key = type(e).__name__
        # 这里没有缓存，因为这个错误是服务器内部检查
        data = dict(status=403,  # status.HTTP_403_FORBIDDEN,
                    datetime=datetime.now().isoformat(),
                    module=module, methods=methods, args=args, kwargs=kwargs)
        data['type'] = type(e).__name__
        data['data'] = repr(e)
        buf = serialize(data).read()

    return key, buf, data


async def _call(user, module, methods, args, kwargs, cache_expire, async_remote):
    """进行实际调用

    将配额计算放在调用第三方代码时，优化用户体验
    """

    # 返回的数据包
    d = dict(status=200,  # status.HTTP_200_OK,
             datetime=datetime.now().isoformat(),  # 加查询时间，缓存中也许可以判断是否过期
             module=module,
             methods=methods,
             args=args,
             kwargs=kwargs)

    try:
        try:
            # 当前server目录下文件，用于特别处理
            api = __import__(f'{__package__}.server.{module}', fromlist=['*'])
        except ModuleNotFoundError as e:
            # 导入系统包
            if module == __package__:
                raise Exception(f'Not Allowed to call {__package__}')
            api = __import__(module, fromlist=['*'])

        # 转成字符串，后面可能于做cache的key
        logger.info(f'Call: {module}::{methods}\t{args}\t{kwargs}'[:200])

        func = api
        for method in methods.split('.'):
            func = getattr(func, method)

        # 可以调用的属性
        if callable(func):
            # 例如os.remove
            type_ = 'function'
            if async_remote:
                func = await to_async(func)(*args, **kwargs)
            else:
                func = to_sync(func)(*args, **kwargs)

        # 结果的类型名
        class_name = func.__class__.__name__

        # 不可调用的直接返回
        if class_name == 'module':
            # 例如os.path，但用法为os.path()
            data = repr(func)
            cache_expire = min(cache_expire, 0)
        elif class_name in ('dict_keys', 'dict_values'):
            # 无法序列化，只能强行转换
            # 例如：sys.modules.keys(), 也可以sys.modules.keys.__list()
            data = list(func)
            cache_expire = min(cache_expire, 0)
        else:
            # 例如math.pi，但用法math.pi()
            data = func

        d['type'] = type(func).__name__
        d['data'] = data

    except Exception as e:
        d['status'] = 500  # status.HTTP_500_INTERNAL_SERVER_ERROR
        d['type'] = type(e).__name__
        d['data'] = repr(e)
        # 错误也缓存一会，防止用户写了死循环搞崩上游
        cache_expire = min(cache_expire, 60)

    # 由于错误信息也想缓存，所以这里进行编码
    buf = serialize(d).read()

    return cache_expire, buf, d
