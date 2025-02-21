# 创建客户连接
from ksrpc import RpcClient
from ksrpc.connections.http import HttpxConnection

conn = HttpxConnection('http://127.0.0.1:8000/api/file')
client = RpcClient('tushare', conn, async_local=False)
client.cache_get = True
client.cache_expire = 86400

# 对原版库进行定制处理，需要已经安装了原版库
from ksrpc.hack.tushare import hack

hack(client)

# 原版代码可都保持不变

import tushare as ts

ts.set_token('TUSHARE_TOKEN')
print(ts.get_token())
pro = ts.pro_api()
df = pro.trade_cal(exchange='', start_date='20210901', end_date='20211231')
print(df)
df = pro.daily(ts_code='000001.SZ,600000.SH', start_date='20180701', end_date='20180718')
print(df)
