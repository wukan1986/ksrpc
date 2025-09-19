import hashlib
import inspect
import sys
from datetime import datetime
from importlib import import_module

from loguru import logger

from ksrpc.serializer.pkl_gzip import serialize

logger.remove()
logger.add(sys.stderr,
           format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level:<8}</level> | PID:{process.id} | TID:{thread.id} | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
           level="INFO", colorize=True)


def make_key(modules_method, args, kwargs):
    """生成缓存key"""
    args_kwargs = f'{modules_method}_{repr(args)}_{repr(kwargs)}'
    if len(args_kwargs) > 32:
        args_kwargs = hashlib.md5(args_kwargs.encode('utf-8')).hexdigest()
    return f'{modules_method}_{args_kwargs}'


async def async_call(modules_method, args, kwargs):
    """简版API调用。没有各种额外功能"""
    key = make_key(modules_method, args, kwargs)

    # 返回的数据包
    d = dict(status=200,  # status.HTTP_200_OK,
             datetime=datetime.now().isoformat(),  # 加查询时间，缓存中也许可以判断是否过期
             modules_method=modules_method,
             args=args,
             kwargs=kwargs)
    try:
        # 多层模块名+一个方法名
        modules, method = modules_method.rsplit('.', 1)
        # 内置在约定目录下的包
        server_modules = f'{__package__}.server.{modules}'
        # 同时存在三个: ksrpc ksrpc.server ksrpc.server.demo
        m = sys.modules.get(server_modules, None) or sys.modules.get(modules, None)

        if m is None:
            try:
                # 当前server目录下文件，用于特别处理
                m = import_module(server_modules)
            except ModuleNotFoundError as e:
                # 导入系统包，自动注册多层到sys.modules
                m = import_module(modules)

            # # 一定要将顶层模块存到globals，这样后面用法就与习惯完全一样。但这处只是为了演示，可跳过
            # top_module = m.__name__.split('.', 1)[0]
            # globals()[top_module] = sys.modules[top_module]
        else:
            # 模块之前已经加载过了
            pass

        # 转成字符串，后面可能于做cache的key
        logger.info(f'{modules_method}\t{args}\t{kwargs}'[:200])

        func = getattr(m, method)
        # # 其实前面全是模块，就最后一个是方法
        # for method in methods.split('.'):
        #     func = getattr(func, method)

        # 可以调用的属性
        if callable(func):
            # 例如os.remove
            type_ = 'function'
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
            # 例如：sys.modules.keys(), 也可以sys.modules.keys.__list()
            data = list(output)
        else:
            # 例如math.pi，但用法math.pi()
            data = output

        d['type'] = type(output).__name__
        d['data'] = data
    except Exception as e:
        d['status'] = 500  # status.HTTP_500_INTERNAL_SERVER_ERROR
        d['type'] = type(e).__name__
        d['data'] = repr(e)

    # 由于错误信息也想缓存，所以这里进行编码
    buf = serialize(d).read()

    return key, buf, d
