"""
TuShare服务转发
1. 屏蔽set_token功能，由服务端进行统一认证
2. 客户端替换了pro, 服务端将请求转到pro

"""
import os

import tushare as ts

# set TUSHARE_TOKEN=23a25f9298a9d6849a1127b8c5f1d3b468f9d3012ed72& python -m ksrpc.run_app
pro = ts.pro_api(token=os.getenv("TUSHARE_TOKEN", ""), timeout=30)

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
