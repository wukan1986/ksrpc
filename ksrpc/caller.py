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


def get_func(module, name):
    # ksrpc.server.demo.CLASS.B.__getitem__(3)，这种格式只能确信第一个是模块，最后一个是方法，其他都不确定
    m = import_module(module)
    for n in name.split('.'):
        if len(n) == 0:
            continue
        if n == "__call__":
            # 默认 __call__ 是传不到服务端的，除非用户主动发起 __getattr__('__call__')
            continue
        elif hasattr(m, n):
            m = getattr(m, n)
        else:
            if n in ("__iter__", "__aiter__", '__next__', '__anext__'):
                # 需要特别处理
                continue
            else:
                m = import_module(f"{m.__name__}.{n}")
    return m


async def async_call(module, name, args, kwargs, ref_id):
    """简版异步API调用。没有各种额外功能"""
    # 返回的数据包
    d = dict(status=200,  # status.HTTP_200_OK,
             datetime=datetime.now().isoformat(),  # 加查询时间，缓存中也许可以判断是否过期
             module=module,
             name=name,
             args=args,
             kwargs=kwargs,
             ref_id=0)
    try:
        # 转成字符串，后面可能于做cache的key
        logger.info(f'{module}::{name}\t{args}\t{kwargs}'[:300])

        # ksrpc.server.demo::async_counter 这里产生的generator，ref_id传到了RpcClient
        # ksrpc.server.demo::async_counter.__aiter__.__anext__ 居然这里将错就错，用上了上次的对象 TODO 这里以后一定要改

        func = get_func(module, name)

        if name.endswith(("__next__", "__anext__")):
            # 不管模块了，直接引用全局变量中的对象
            try:
                ref = globals()[ref_id]
                # 兼容同步和异步
                if hasattr(ref, "__anext__"):
                    output = await ref.__anext__()
                else:
                    output = ref.__next__()
            except (StopIteration, StopAsyncIteration):
                # 迭代完成，移出
                globals().pop(ref_id, None)
                # StopIteration强制转换成异步
                raise StopAsyncIteration()
            except KeyError:
                raise StopAsyncIteration()
        else:
            if name.endswith("__func__"):  # isinstance(func, types.FunctionType) # 不行
                # print(ksrpc.server.demo.p.__format__.__func__)
                output = func
            elif isinstance(func, type):
                # print(ksrpc.server.demo.p.__class__)
                output = func
            # 可以调用的属性
            elif callable(func) or name.endswith("__call__"):
                # __call__不合语法，但与本地报错效果一致了
                if inspect.iscoroutinefunction(func):
                    output = await func(*args, **kwargs)
                else:
                    output = func(*args, **kwargs)
            else:
                output = func

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

    return d


async def process_call(module, name, args, kwargs, ref_id):
    """进程版API调用。结束后进程退出自动释放内存

    Notes
    =====
    启动了一个新进程速度显著下降，但与网络传输大数据相比可以忽略不计。
    获得好处是释放了内存，适合内存有限的平台

    """
    with ProcessPoolExecutor(max_workers=1) as executor:
        future = executor.submit(async_wrapper, async_call, module, name, args, kwargs, ref_id)
        return future.result()


async def switch_call(module, name, args, kwargs, ref_id):
    if CALL_IN_NEW_PROCESS:
        return await process_call(module, name, args, kwargs, ref_id)
    else:
        return await async_call(module, name, args, kwargs, ref_id)
