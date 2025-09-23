import hashlib
import inspect
import sys
import types
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from importlib import import_module

from loguru import logger

from ksrpc.config import CALL_IN_NEW_PROCESS
from ksrpc.utils.async_ import async_wrapper

logger.remove()
logger.add(sys.stderr,
           format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level:<8}</level> | PID:{process.id} | TID:{thread.id} | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
           level="INFO", colorize=True)


def make_key(module, name, args, kwargs):
    """生成缓存key"""
    key = f'{module}::{name}_{repr(args)}_{repr(kwargs)}'
    return hashlib.md5(key.encode('utf-8')).hexdigest()


def get_func(module, name):
    # ksrpc.server.demo.CLASS.B.__getitem__(3)，这种格式只能确信第一个是模块，最后一个是方法，其他都不确定
    m = import_module(module)
    for n in name.split('.'):
        if len(n) == 0:
            continue
        if hasattr(m, n):
            m = getattr(m, n)
        else:
            m = import_module(f"{m.__name__}.{n}")
    return m


async def async_call(module, name, args, kwargs):
    """简版异步API调用。没有各种额外功能"""
    key = make_key(module, name, args, kwargs)

    # 返回的数据包
    d = dict(status=200,  # status.HTTP_200_OK,
             datetime=datetime.now().isoformat(),  # 加查询时间，缓存中也许可以判断是否过期
             module=module,
             name=name,
             args=args,
             kwargs=kwargs)
    try:
        # 转成字符串，后面可能于做cache的key
        logger.info(f'{module}::{name}\t{args}\t{kwargs}'[:300])

        func = get_func(module, name)

        if isinstance(func, type):
            # print(ksrpc.server.demo.p.__class__)
            output = func
        elif name.endswith(".__func__"): # isinstance(func, types.FunctionType) # 不行
            # print(ksrpc.server.demo.p.__format__.__func__)
            output = func
        # 可以调用的属性
        elif callable(func):
            # 例如os.remove
            if inspect.iscoroutinefunction(func):
                output = await func(*args, **kwargs)
            else:
                output = func(*args, **kwargs)
        else:
            output = func

        d['type'] = type(output).__name__
        d['data'] = output
    except Exception as e:
        d['status'] = 500  # status.HTTP_500_INTERNAL_SERVER_ERROR
        d['type'] = type(e).__name__
        d['data'] = repr(e)

    return key, d


async def process_call(module, name, args, kwargs):
    """进程版API调用。结束后进程退出自动释放内存

    Notes
    =====
    启动了一个新进程速度显著下降，但与网络传输大数据相比可以忽略不计。
    获得好处是释放了内存，适合内存有限的平台

    """
    with ProcessPoolExecutor(max_workers=1) as executor:
        future = executor.submit(async_wrapper, async_call, module, name, args, kwargs)
        return future.result()


async def switch_call(module, name, args, kwargs):
    if CALL_IN_NEW_PROCESS:
        return await process_call(module, name, args, kwargs)
    else:
        return await async_call(module, name, args, kwargs)
