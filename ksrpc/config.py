"""
全局开关
!!!中继功能不需修改，提供服务功能需要手工开启
"""
# 是否可以调用当前服务器中的Python库
# 为了安全，默认关闭，有需要用户请修改配置
ENABLE_SERVER = False
# 是否启用中继功能。启用此功能可实现反向RPC功能。
# 此功能只转发请求，并不执行其中的内容，对当前中继服务器没有安全威胁
# 鼓励有公网IP的用户开放提供此功能
ENABLE_RELAY = True

"""
服务端配置
"""
HOST = '0.0.0.0'
PORT = 8000
"""
是否检查可调用的方法。
!!! 生产环境中请不要随意关闭，否则权限过大
"""
METHODS_CHECK = False

# 允许的方法
# 没有列出的module和method默认值为False表示不可调用
METHODS_ALLOW = {
    'pandas': {
        'read_csv': True,
        'util': {
            'testing': {
                'makeTimeDataFrame': True,
                'makeDataFrame': False,
            }
        }
    },
    'os': True,
    'ntpath': True,
    'numpy': True,
    'math': True,
    'sys': True,
    'jqdatasdk': True,
    'WindPy': True,
    'tushare': True,
    'rqdatac': True,
    'demo': True,
    'xbbg': True,
    'eikon': True,
}

# 禁止的方法
# 没有列出的module和method默认值为True表示放行
METHODS_BLOCK = {
    'os': {
        'remove': False,
    },
    'ksrpc': {
        'config': False,  # !!!一定要注意此处，否则客户端可以盗取账号
    }
}

"""
是否进行IP检查，可屏蔽外网访问
"""
IP_CHECK = False

IP_ALLOW = {
    '127.0.0.0/8': True,  # 回环地址
    '192.168.0.0/16': True,  # C类内网
    '172.16.0.0/12': True,  # B类内网
    '10.0.0.0/8': True,  # A类内网
}
IP_BLOCK = {
    '8.8.8.8/32': False,
    '8.8.4.4/32': False,
}

"""
是否启用授权
"""
AUTH_CHECK = False
# API授权
AUTH_TOKENS = {
    "secret-token-1": "john",
    "secret-token-2": "susan",
}

"""
是否进行配额检查，可限制用户超量下载
只限制初始请求数据，第二次请求走缓存不消耗配额
"""
QUOTA_CHECK = False

QUOTA_MODULE = {
    'demo': 1000,
}

QUOTA_FUNC = {
    'demo': {
        'test': 500,
    }
}
QUOTA_MODULE_DEFAULT = 10000 * 10000  # 1亿行
QUOTA_FUNC_DEFAULT = 10000 * 1000  # 1千万行

# 缓存类型。生产环境请配置redis服务
CACHE_TYPE = 'fakeredis'  # fakeredis, aioredis
# 缓存服务地址
REDIS_URL = "redis://:password@localhost:6379/0"

# 聚宽账号
JQ_USERNAME = '13912345678'
JQ_PASSWORD = '12345678'

# TuShare账号
TUSHARE_TOKEN = '12345678'

# eikon账号
EIKON_APP_KEY = '12345678'

# 米筐账号
RQ_USERNAME = '13912345678'
RQ_PASSWORD = '12345678'

# 启用万得
WIND_ENABLE = False

# 打印当前配置
print('current config:', __file__)
