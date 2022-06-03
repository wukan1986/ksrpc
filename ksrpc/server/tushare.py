"""
TuShare服务转发
1. 屏蔽set_token功能，由服务端进行统一认证
2. 客户端替换了pro, 服务端将请求转到pro

"""

import tushare as ts

from ..config import TUSHARE_TOKEN

ts.set_token(TUSHARE_TOKEN)
# 用完后清空，防止被客户端获取
del TUSHARE_TOKEN
pro = ts.pro_api()

__path__ = []
__all__ = []


def __getattr__(name):
    return pro.__getattr__(name)


def set_token(token):
    # 防止用户调用到了pro.set_token
    pass


def get_token():
    return ""


def pro_api(token='', timeout=30):
    # 防止用户调用到了pro.pro_api
    pass
