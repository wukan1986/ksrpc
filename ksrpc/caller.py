import builtins
import fnmatch
import hashlib
import inspect
import pathlib
import pickle
import sys
import time
import traceback
import types
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from importlib import import_module

from loguru import logger

from ksrpc.client import RpcClient, _Self
from ksrpc.config import IMPORT_RULES, CACHE_ENABLE, CACHE_PATH, CACHE_TIMEOUT
from ksrpc.utils.async_ import async_to_sync

CACHE = pathlib.Path(CACHE_PATH)
if CACHE_ENABLE:
    # 需要有创建文件夹的权限
    CACHE.mkdir(parents=True, exist_ok=True)

logger.remove()
logger.add(sys.stderr,
           format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level:<8}</level> | PID:{process.id} | TID:{thread.id} | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
           level="INFO", colorize=True)


async def get_property(obj, ref_id):
    """如果是特殊的RpcClient，得到对应的属性"""
    if isinstance(obj, RpcClient):
        return await get_calls(obj._module, obj._calls, ref_id)
    return obj


def replace_self(self, value):
    """Self替换"""
    return value if isinstance(self, _Self) else self


def is_import_allowed(module_name, rules):
    for pattern, allowed in rules.items():
        if fnmatch.fnmatch(module_name, pattern):
            return allowed
    return False


def import_module_allowed(module):
    m = import_module(module)
    assert is_import_allowed(m.__name__, IMPORT_RULES), f"import {m.__name__} not allowed"
    return m


async def get_calls(module, calls, ref_id):
    """根据模块和函数名列表，得到函数"""
    # ksrpc.server.demo::async_counter 这里产生的generator，ref_id传到了RpcClient
    # ksrpc.server.demo::async_counter.__aiter__.__anext__ 居然这里将错就错，用上了上次的对象 TODO 这里以后一定要改
    out = import_module_allowed(module)
    for c in calls:
        update = False
        func = None
        if len(c.name) == 0:
            continue

        # 先查属性，再查模块，最后查builtins
        if hasattr(out, c.name):
            out = getattr(out, c.name)
            update = True
        elif inspect.ismodule(out):
            if c.name == "generate_stub":
                from ksrpc.utils.stubs import generate_stub
                # 添加的额外函数，用于生成存根文件
                c.kwargs['file'] = out.__file__
                logger.info('generate_stub: {} {}', c.args, c.kwargs)
                out = generate_stub
                update = True
            else:
                try:
                    out = import_module_allowed(f"{out.__name__}.{c.name}")
                    update = True
                except ModuleNotFoundError:
                    update = False

        if not update and hasattr(builtins, c.name):
            # 需要在config.py IMPORT_RULES中开放builtins导入权限
            import_module_allowed(builtins.__name__)
            # 这个功能有一定的危险性
            func = getattr(builtins, c.name)
            update = True

        # 迭代器方法
        if c.name in ('__next__', '__anext__'):
            try:
                ref = globals()[ref_id]
                # 兼容同步和异步
                if hasattr(ref, "__anext__"):
                    out = await ref.__anext__()
                else:
                    out = ref.__next__()
            except (StopIteration, StopAsyncIteration) as e:
                # 迭代完成，移出
                globals().pop(ref_id, None)
                # StopIteration强制转换成异步
                raise StopAsyncIteration() from e
            except KeyError as e:
                raise StopAsyncIteration() from e
            update = True
            return out

        assert update, f"getattr(,{c.name}) failed"

        if c.args is not None:
            # 特别处理，对RpcClient进行转换
            c.args = [await get_property(a, ref_id) for a in c.args]
            c.kwargs = {k: await get_property(v, ref_id) for k, v in c.kwargs.items()}
            #
            if len(c.args) > 0 and func:
                # 检查是否有_Self，开始替换
                args = [replace_self(a, out) for a in c.args]
                kwargs = {k: replace_self(v, out) for k, v in c.kwargs.items()}
                if (c.args != args) or (c.kwargs != kwargs):
                    # 特殊转换代码，如int()功能
                    logger.info(f'{c}: {c.name}({out}...)')
                    out = func
            else:
                args = c.args
                kwargs = c.kwargs

            if callable(out) or c.name.endswith("__call__"):
                if inspect.iscoroutinefunction(out):
                    out = await out(*args, **kwargs)
                else:
                    out = out(*args, **kwargs)
        else:
            # 获取的是属性，可直接返回
            pass

    return out


def call_chian(module, calls):
    """调用链条，可用与权限判断"""
    return '.'.join([module] + [c.name for c in calls])


def chian_timeout(chian, timeouts):
    for pattern, timeout in timeouts.items():
        if fnmatch.fnmatch(chian, pattern):
            return timeout
    return 0


def generate_key(module, calls) -> str:
    """生成唯一key, 用于缓存ID"""
    pickled = pickle.dumps((module, calls))
    return hashlib.md5(pickled).hexdigest()


async def async_call(module, calls, ref_id):
    """简版异步API调用。没有各种额外功能"""
    # 返回的数据包
    d = dict(status=200,  # status.HTTP_200_OK,
             datetime=datetime.now().isoformat(),  # 加查询时间，缓存中也许可以判断是否过期
             module=module,
             calls=calls,
             ref_id=0)
    try:
        if CACHE_ENABLE:
            # 缓存ID与超时
            cache_key = generate_key(module, calls)
            cache_timeout = chian_timeout(call_chian(module, calls), CACHE_TIMEOUT)
            path = CACHE / cache_key
            leave = path.stat().st_mtime + cache_timeout - time.time()
            if path.exists() and leave > 0:
                logger.info(f'load {leave:.1f} {cache_key} {module}:{calls}'[:300])
                with path.open("rb") as f:
                    output = pickle.load(f)
            else:
                logger.info(f'dump {cache_timeout} {cache_key} {module}:{calls}'[:300])
                output = await get_calls(module, calls, ref_id)
                with path.open("wb") as f:
                    pickle.dump(output, f)
        else:
            logger.info(f'call {module}:{calls}'[:300])
            output = await get_calls(module, calls, ref_id)

        if isinstance(output, (types.GeneratorType, types.AsyncGeneratorType)):
            # 处理生成器。需要传引用ref_id,提供给__next__使用
            ref_id = id(output)
            globals()[ref_id] = output  # 一定要记得释放
            d['ref_id'] = ref_id
            output = None  # 生成器不可序列化，传空过去

        d['type'] = type(output).__name__
        d['data'] = output
    except Exception as e:
        d['status'] = 500  # status.HTTP_500_INTERNAL_SERVER_ERROR
        d['type'] = type(e).__name__
        d['data'] = e  # 是否有无法序列化的异常?
        d['traceback'] = traceback.format_exc()

    return d


async def process_call(module, calls, ref_id):
    """进程版API调用。结束后进程退出自动释放内存

    Notes
    =====
    启动了一个新进程速度显著下降，但与网络传输大数据相比可以忽略不计。
    获得好处是释放了内存，适合内存有限的平台

    """
    with ProcessPoolExecutor(max_workers=1) as executor:
        future = executor.submit(async_to_sync, async_call, module, calls, ref_id)
        return future.result()


async def switch_call(module, calls, ref_id):
    """
    TODO 在新进程中调用开关，可以手工设置为True/False

    启动新进程会消耗一点时间，但相对网络传输大数据可以忽略不计
    获得的好处是新进程会自动退出释放内存减少崩溃，适合在云服务器中运行
    """
    import os

    CALL_IN_NEW_PROCESS = hasattr(os, 'fork')
    print(f"CALL_IN_NEW_PROCESS = {CALL_IN_NEW_PROCESS}")

    if CALL_IN_NEW_PROCESS:
        return await process_call(module, calls, ref_id)
    else:
        return await async_call(module, calls, ref_id)
