"""
rqdatac服务转发
1. 屏蔽init功能，由服务端进行统一认证
2. 客户端替换了client, 服务端将请求转到client，统一进行execute

"""
from atexit import register

from loguru import logger
from rqdatac import init, reset
from rqdatac.client import get_client

from ..config import RQ_USERNAME, RQ_PASSWORD

init(username=RQ_USERNAME, password=RQ_PASSWORD)
# 用完后清空，防止被客户端获取
del RQ_USERNAME
del RQ_PASSWORD


@register
def _atexit():
    logger.info("{} {}", __name__, _atexit.__name__)
    reset()


def execute(method, *args, **kwargs):
    return get_client().execute(method, *args, **kwargs)


def init(username=None, password=None, addr=("rqdatad-pro.ricequant.com", 16011), *_, **kwargs):
    # 防止用户调用到了init
    pass
