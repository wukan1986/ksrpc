import os as _os  # noqa
import sys as _sys  # noqa

"""
TODO Web服务配置。不建议直接使用默认值
"""
HOST = "0.0.0.0"
PORT = 8080
# HTTP与WebSocket地址可以相同也可以不同。设置成一样可以减少用户困惑
PATH_HTTP = "/api/v1/{time}"  # HTTP服务向外提供路径。{time}表示时间动态URL，与服务器误差15秒内才能访问
PATH_WS = "/api/v1/{time}"  # WebSocket服务向外提供路径。{time}表示时间动态URL，与服务器误差15秒内才能访问

"""
TODO Basic认证。一定不要使用默认值
"""
USER_CREDENTIALS = {
    "用户名": "密码",
    "admin": "password123",
    "user": "secret",
}

"""
TODO 导入规则。按顺序检查规则，遇到匹配直接返回

向外部提供服务时，如“ksrpc.server.demo”,建议
"ksrpc*": True,
"*": False,

向内部提供服务时，可直接
"*": True

注意：以下是有区别的
ksrpc.* # 所有子模块
ksrpc* # 当前模块和子模块

"""
IMPORT_RULES = {
    "ksrpc.server.demo": True,
    "ksrpc.server.*": False,

    "builtins": True,  # Self语法支持须允许。注意：open/exec/eval等风险大
    "*": True,  # 全部允许。支持分步导入，如：先导入`ksrpc.server`再导入`demo`
    # "*": False,  # 全部拒绝。拒绝分步导入，如：必需直接导入`ksrpc.server.demo`
}

"""
TODO 在新进程中调用开关，可以手工设置为True/False

启动新进程会消耗一点时间，但相对网络传输大数据可以忽略不计
获得的好处是新进程会自动退出释放内存减少崩溃，适合在云服务器中运行
"""
CALL_IN_NEW_PROCESS = hasattr(_os, 'fork')
print(f"CALL_IN_NEW_PROCESS = {CALL_IN_NEW_PROCESS}")
