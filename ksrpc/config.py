import os

"""
Web服务配置。不建议使用默认值
"""
HOST = "0.0.0.0"
PORT = 8080
PATH_HTTP = "/api/v1/{time}"  # HTTP服务向外提供路径。{time}表示时间动态URL，与服务器误差15秒内才能访问
PATH_WS = "/ws/v1/{time}"  # WebSocket服务向外提供路径。{time}表示时间动态URL，与服务器误差15秒内才能访问

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
