import asyncio
import hashlib
import inspect
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from importlib import import_module

from loguru import logger

from ksrpc.config import CALL_IN_NEW_PROCESS

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
        logger.info(f'{module}::{name}\t{args}\t{kwargs}'[:200])

        func = get_func(module, name)

        # 可以调用的属性
        if callable(func):
            # 例如os.remove
            if inspect.iscoroutinefunction(func):
                output = await func(*args, **kwargs)
            else:
                output = func(*args, **kwargs)
        else:
            output = func

        # 结果的类型名
        class_name = output.__class__.__name__

        # 不可调用的直接返回
        if class_name == 'module':
            # 例如os.path，但用法为os.path()
            data = repr(output)
        elif class_name in ('dict_keys', 'dict_values'):
            # 无法序列化，只能强行转换
            # 例如：sys.modules.keys()
            data = list(output)
        else:
            # 例如math.pi，但得加()才能触发，math.pi()
            data = output

        d['type'] = type(output).__name__
        d['data'] = data
    except Exception as e:
        d['status'] = 500  # status.HTTP_500_INTERNAL_SERVER_ERROR
        d['type'] = type(e).__name__
        d['data'] = repr(e)

    return key, d


def async_wrapper(func, *args, **kwargs):
    try:
        # 尝试使用 Python 3.7+ 的 asyncio.run()
        return asyncio.run(func(*args, **kwargs))
    except AttributeError:
        # 回退到手动事件循环管理
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(func(*args, **kwargs))
        finally:
            loop.close()


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
