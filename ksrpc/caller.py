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

import numpy as np
import pandas as pd
from loguru import logger
from revolving_asyncio import to_async, to_sync

from .cache import async_cache_get, async_cache_setex, async_cache_incrby
from .caller_simple import make_key
from .config import QUOTA_CHECK, IP_ALLOW, IP_BLOCK, IP_CHECK, METHODS_CHECK, ENABLE_SERVER
from .model import RspModel
from .serializer.pkl_gzip import serialize
from .utils.check_ import check_methods, check_ip, get_quota


def before_call(host, user, func):
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

    methods = func.split('.')

    if METHODS_CHECK:
        if not check_methods(METHODS_ALLOW, methods, False):
            raise Exception(f'Method Not Allowed, {func} not in allowlist')
        if not check_methods(METHODS_BLOCK, methods, True):
            raise Exception(f'Method Not Allowed, {func} in blocklist')


async def call(user, func, args, kwargs, cache_get, cache_expire, async_remote, fmt=None):
    try:
        buf = None
        data = None  # None表示从缓存中取的，需要其它格式时需要转换
        # cache所用的key
        key = make_key(func, args, kwargs)

        if cache_get:
            # 优先取缓存
            buf = await async_cache_get(key)
        if buf is None:
            cache_expire, buf, data = await _call(user, func, args, kwargs, cache_expire, async_remote)

            # 过短的缓存时间没有必要
            if cache_expire >= 30:
                # 就算强行去查询数据，也会想办法存下，再次取时还能从缓存中取
                await async_cache_setex(key, cache_expire, buf)
                logger.info(f'To cache: expire:{cache_expire}\tlen:{len(buf)}\t{key}')
        else:
            logger.info(f'From cache: {func}\t{args}\t{kwargs}')

    except Exception as e:
        key = type(e).__name__
        # 这里没有缓存，因为这个错误是服务器内部检查
        data = RspModel(status=403,  # status.HTTP_403_FORBIDDEN,
                        datetime=datetime.now().isoformat(),
                        func=func, args=args, kwargs=kwargs)
        data.type = type(e).__name__
        data.data = repr(e)
        data = data.model_dump() if hasattr(data, 'model_dump') else data.dict()
        buf = serialize(data).read()

    return key, buf, data


async def _call(user, func_name, args, kwargs, cache_expire, async_remote):
    """进行实际调用

    将配额计算放在调用第三方代码时，优化用户体验
    """

    methods = func_name.split('.')
    module = methods[0]

    # 返回的数据包
    d = RspModel(status=200,  # status.HTTP_200_OK,
                 datetime=datetime.now().isoformat(),  # 加查询时间，缓存中也许可以判断是否过期
                 func=func_name,
                 args=args,
                 kwargs=kwargs)

    methods = methods[1:]
    try:
        m_quota_key = f'QUOTA/{user}/{module}'
        f_quota_key = f'QUOTA/{user}/{func_name}'
        if QUOTA_CHECK:
            # 配额检查
            from .config import QUOTA_MODULE, QUOTA_MODULE_DEFAULT, QUOTA_FUNC, QUOTA_FUNC_DEFAULT

            m_quota = int(await async_cache_get(m_quota_key) or 0)
            f_quota = int(await async_cache_get(f_quota_key) or 0)
            quota = get_quota(QUOTA_FUNC, methods, QUOTA_FUNC_DEFAULT)
            if f_quota > quota:
                raise Exception(f'Over quota: user:{user}, {func_name}:{f_quota}>{quota}')
            quota = get_quota(QUOTA_MODULE, [module], QUOTA_MODULE_DEFAULT)
            if m_quota > quota:
                raise Exception(f'Over quota: user:{user}, {module}:{quota}')

        try:
            # 当前server目录下文件，用于特别处理
            api = __import__(f'{__package__}.server.{module}', fromlist=['*'])
        except ModuleNotFoundError as e:
            # 导入系统包
            if module == __package__:
                raise Exception(f'Not Allowed to call {__package__}')
            api = __import__(module, fromlist=['*'])

        # 转成字符串，后面可能于做cache的key
        logger.info(f'Call: {func_name}\t{args}\t{kwargs}'[:200])

        func = api
        for method in methods:
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

            if QUOTA_CHECK:
                # 模块和函数都进行配额统计，是按行记（聚宽），按单元格记（万得），还是按调用次数记？
                if isinstance(data, (pd.DataFrame, pd.Series, np.ndarray, list)):
                    # # 按调用次数
                    # await async_cache_incrby(m_quota_key, 1)
                    # await async_cache_incrby(f_quota_key, 1)

                    # 按行统计
                    await async_cache_incrby(m_quota_key, len(data))
                    await async_cache_incrby(f_quota_key, len(data))

                    # # 按单元格统计
                    # if hasattr(data, 'size'):
                    #     await async_cache_incrby(m_quota_key, data.size)
                    #     await async_cache_incrby(f_quota_key, data.size)
                    # else:
                    #     await async_cache_incrby(m_quota_key, len(data))
                    #     await async_cache_incrby(f_quota_key, len(data))

        d.type = type(func).__name__
        d.data = data

        # pkl序列化，为了能完整还源
        d = d.model_dump() if hasattr(d, 'model_dump') else d.dict()
        buf = serialize(d).read()

    except Exception as e:
        d.status = 500  # status.HTTP_500_INTERNAL_SERVER_ERROR
        d.type = type(e).__name__
        d.data = repr(e)
        # 错误也缓存一会，防止用户写了死循环搞崩上游
        cache_expire = min(cache_expire, 60)
        d = d.model_dump() if hasattr(d, 'model_dump') else d.dict()
        # 由于错误信息也想缓存，所以这里进行编码
        buf = serialize(d).read()

    return cache_expire, buf, d
