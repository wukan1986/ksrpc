import nest_asyncio

from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection

URL_HTTP = 'http://127.0.0.1:8080/api/v1/{time}'

USERNAME = 'admin'
PASSWORD = 'password123'

# 必用，否则同步模式只能调用第一次，第二次会报 RuntimeError: Event loop is closed
nest_asyncio.apply()

conn = HttpConnection(URL_HTTP, USERNAME, PASSWORD)
client = RpcClient('ksrpc.server.tushare', conn, to_sync=True)
# =================================

# 对原版库进行定制处理，需要已经安装了原版库
from ksrpc.hack.tushare import hack

hack(client)
# =================================

# 官方测试代码
import os

import tushare as ts

pro = ts.pro_api(token=os.getenv("TUSHARE_TOKEN"), timeout=30)

df = pro.daily(ts_code='000001.SZ', start_date='20180701', end_date='20180718')

print(df)
