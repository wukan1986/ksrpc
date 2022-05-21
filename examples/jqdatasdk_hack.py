# 创建客户连接

from ksrpc import RpcClient
from ksrpc.connections.http import HttpxConnection

conn = HttpxConnection('http://127.0.0.1:8000/api')
conn.timeout = None
client = RpcClient('jqdatasdk', conn, is_async=False)
client.cache_get = True
client.cache_expire = 86400

# 对原版库进行定制处理，需要已经安装了原版库
from ksrpc.hack.jqdatasdk import hack

hack(client)

# 原版代码可都保持不变
from jqdatasdk import *

auth('JQ_USERNAME', 'JQ_PASSWORD')

df = get_extras('is_st', ['000001.XSHE', '000018.XSHE'], start_date='2021-09-01', end_date=datetime.now(), df=False)
print(df)

# df = get_security_info('000001.XSHE')
# print(df)

df = get_industry_stocks('I64')
print(df)

from jqdatasdk import query, valuation

q = query(
    valuation.code, valuation.day, valuation.turnover_ratio
).filter(
    valuation.code.in_(['000001.XSHE'])
)

df = get_fundamentals(q, date='2021-09-22')
print(df)

df = technical_analysis.MACD(['000001.XSHE'], '2021-09-21', SHORT=12, LONG=26, MID=9, unit='1d',
                             include_now=True)
diffD, deaD, macdD = df
print(macdD)

df = get_bars('000001.XSHE', 5, unit='120m', fields=['date', 'open', 'close', 'high', 'low', 'volume', 'money'],
              include_now=False, end_dt='2021-09-29')
print(df)
