#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author     :wukan
# @License    :(C) Copyright 2022, wukan
# @Date       :2022-05-15
"""
缓存
将查询的结果缓存起来，减少对外部数据源的压力，减少限额消耗
"""
from .config import CACHE_TYPE

# 测试时使用的内存redis
if CACHE_TYPE == 'fakeredis':
    import fakeredis

    cache = fakeredis.FakeStrictRedis()
    cache_is_async = False

# 异步版Redis
if CACHE_TYPE == 'aioredis':
    import aioredis
    from .config import REDIS_URL

    cache = aioredis.StrictRedis.from_url(REDIS_URL)
    cache_is_async = True


async def async_cache_get(name):
    """统一缓存读取方式"""
    if cache_is_async:
        return await cache.get(name)
    # 阻塞方式调用
    return cache.get(name)


async def async_cache_setex(name, time, value):
    """统一缓存写入方式"""
    if cache_is_async:
        return await cache.setex(name, time, value)
    # 阻塞方式调用
    cache.setex(name, time, value)
