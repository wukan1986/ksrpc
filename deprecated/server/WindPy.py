"""
Wind服务转发
1. 必须先开启Wind客户端再启动此服务
2. 返回的数据做了额外处理，额外抛出异常，用于控制缓存
"""
from functools import wraps

from WindPy import w

# TODO: 是否能在线程中启动，需要测试
# print(w.start())

__path__ = []
__all__ = []


def _post_func(func, name):
    @wraps(func)
    def decorated(*args, **kwargs):
        # print(name)
        # 是否能获取到函数名
        error, data = func(*args, **kwargs)
        # 原始错误上层无法感知，导致可能按用户指定的时间缓存一天
        # 所以特别处理一下，遇到错误抛出异常，这样上层就能识别将缓存缩短成1分钟
        if error != 0:
            raise Exception(data)
        return error, data

    return decorated


def __getattr__(name):
    # 对数据做后处理
    return _post_func(getattr(w, name), name)


def start():
    pass
