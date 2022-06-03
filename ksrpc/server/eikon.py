import eikon as ek

from ..config import EIKON_APP_KEY

ek.set_app_key(EIKON_APP_KEY)
# 用完后清空，防止被客户端获取
del EIKON_APP_KEY


def set_app_key(app_key):
    pass


def get_app_key():
    return ""


def __getattr__(name):
    return ek.__getattr__(name)
