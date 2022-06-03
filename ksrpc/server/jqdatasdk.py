"""
jqdatasdk服务转发
1. jqdatasdk中多线程时会多次登录，实现不重复登录
2. 替换底层
"""
from atexit import register

from jqdatasdk.client import JQDataClient
from loguru import logger


class HackThreadingLocal:
    _instance = None


# 解决多线程时多次登录问题
JQDataClient._threading_local = HackThreadingLocal()

from jqdatasdk import auth as _auth
from jqdatasdk import is_auth as _is_auth
from jqdatasdk import logout as _logout


@register
def _atexit():
    logger.info("{} {}", __name__, _atexit.__name__)
    _logout()


__path__ = []
__all__ = []


def __getattr__(name):
    # 登录认证，争取只做一次
    if not _is_auth():
        from ..config import JQ_USERNAME, JQ_PASSWORD

        _auth(JQ_USERNAME, JQ_PASSWORD)
        # 用完后清空，防止被客户端获取
        del JQ_USERNAME
        del JQ_PASSWORD

    return JQDataClient.instance().__getattr__(name)


def auth(username, password, host=None, port=None):
    pass


def logout():
    pass
