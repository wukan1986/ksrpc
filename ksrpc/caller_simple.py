import hashlib
import os
import threading
from datetime import datetime

from revolving_asyncio import to_sync

from ksrpc.serializer.pkl_gzip import serialize


def make_key(func, args, kwargs):
    """生成缓存key"""
    args_kwargs = f'{func}_{repr(args)}_{repr(kwargs)}'
    if len(args_kwargs) > 32:
        args_kwargs = hashlib.md5(args_kwargs.encode('utf-8')).hexdigest()
    return f'{func}_{args_kwargs}'


def simple_call(func_name, args, kwargs):
    """简版API调用。没有各种额外功能"""
    key = make_key(func_name, args, kwargs)

    methods = func_name.split('.')
    module = methods[0]

    # 返回的数据包
    d = dict(status=200,  # status.HTTP_200_OK,
             datetime=datetime.now().isoformat(),  # 加查询时间，缓存中也许可以判断是否过期
             func=func_name,
             args=args,
             kwargs=kwargs)

    methods = methods[1:]

    try:

        try:
            # 当前server目录下文件，用于特别处理
            api = __import__(f'{__package__}.server.{module}', fromlist=['*'])
        except ModuleNotFoundError as e:
            # 导入系统包
            if module == __package__:
                raise Exception(f'Not Allowed to call {__package__}')
            api = __import__(module, fromlist=['*'])

        pid = os.getpid()
        tid = threading.get_ident()
        # 转成字符串，后面可能于做cache的key
        print(f'{pid}:{tid}:\t{func_name}\t{args}\t{kwargs}'[:200])

        func = api
        for method in methods:
            func = getattr(func, method)

        # 可以调用的属性
        if callable(func):
            # 例如os.remove
            type_ = 'function'
            func = to_sync(func)(*args, **kwargs)

        # 结果的类型名
        class_name = func.__class__.__name__

        # 不可调用的直接返回
        if class_name == 'module':
            # 例如os.path，但用法为os.path()
            data = repr(func)
        elif class_name in ('dict_keys', 'dict_values'):
            # 无法序列化，只能强行转换
            # 例如：sys.modules.keys(), 也可以sys.modules.keys.__list()
            data = list(func)
        else:
            # 例如math.pi，但用法math.pi()
            data = func

        d['type'] = type(func).__name__
        d['data'] = data

        # pkl序列化，为了能完整还源
        buf = serialize(d).read()

    except Exception as e:
        d['status'] = 500  # status.HTTP_500_INTERNAL_SERVER_ERROR
        d['type'] = type(e).__name__
        d['data'] = repr(e)

        # 由于错误信息也想缓存，所以这里进行编码
        buf = serialize(d).read()

    return key, buf, d
