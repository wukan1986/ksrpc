import os

from ksrpc.utils.urls import BaseURL, TimeURL  # noqa

"""
Web服务配置
"""
HOST = "0.0.0.0"
PORT = 8080

"""
TODO Basic认证。一定要修改账号，不要使用默认值
"""
USER_CREDENTIALS = {
    "用户名": "密码",
    "admin": "password123",
    "user": "secret",
}

"""
TODO 在新进程中调用开关，可以手工设置为True/False

启动新进程会消耗一点时间，但相对网络传输大数据可以忽略不计
获得的好处是新进程会自动退出释放内存减少崩溃，适合在云服务器中运行
"""
CALL_IN_NEW_PROCESS = hasattr(os, 'fork')
print(f"CALL_IN_NEW_PROCESS = {CALL_IN_NEW_PROCESS}")

"""
TODO 为防路径扫描，可以使用动态路径
"""
URL_CHECKER = BaseURL()  # BaseURL(), TimeURL()

print(f"Current config:", __file__)
