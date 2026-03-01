import os as _os  # noqa
import sys as _sys  # noqa

"""
TODO Web服务配置。不建议直接使用默认值
"""
# run_app时有效，gunicorn时看--bind
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
    "ksrpc.server.tushare": True,  # 代理，解决登录问题
    "tushare": False,  # 禁止直接调用
    "ksrpc.server.*": False,

    "builtins": True,  # Self语法支持须允许。注意：open/exec/eval等风险大
    "*": True,  # 全部允许。支持分步导入，如：先导入`ksrpc.server`再导入`demo`
    # "*": False,  # 全部拒绝。拒绝分步导入，如：必需直接导入`ksrpc.server.demo`
}

# 本地缓存超时功能，单位秒，用户需要根据需求自己改动
# 没有提供缓存自动删除功能，你可以考虑crontab -e编辑cron任务，例如凌晨4点执行。注意使用绝对路径
# 0 4 * * * rm -rf /path/to/cache/*
CACHE_ENABLE = False
CACHE_PATH = "cache"
CACHE_TIMEOUT = {
    "ksrpc.server.tushare.daily": 30,
    "ksrpc.server.tushare.*": 60,
    "*": 600,
}

print(__file__)
