# 创建客户连接
from ksrpc.client import RpcProxy
from ksrpc.connections.http import HttpConnection

conn = HttpConnection('http://127.0.0.1:8000/api/file')
client = RpcProxy('tushare', conn)

# import tushare as ts
#
# ts.set_token('TUSHARE_TOKEN')

# pro = ts.pro_api()
pro = client  # 替换，实现之后的代码不改

df = pro.trade_cal(exchange='', start_date='20210901', end_date='20211231')

print(df)
