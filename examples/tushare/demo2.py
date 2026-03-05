"""
仅技术交流演示，请购买数据授权
"""
import os

os.environ["PRINT_PROGRESS"] = "0"

import nest_asyncio

from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection

URL = 'http://127.0.0.1:8080/api/v1'

USERNAME = 'admin'
PASSWORD = 'password123'

# 必用，否则同步模式只能调用第一次，第二次会报 RuntimeError: Event loop is closed
nest_asyncio.apply()

conn = HttpConnection(URL, USERNAME, PASSWORD)
pro = RpcClient('ksrpc.server.tushare', conn, to_sync=True)

df = pro.daily(ts_code='000001.SZ', start_date='20180701', end_date='20180718')

print(df)
