from ksrpc import RpcClient
from ksrpc.connections.http import HttpxConnection

conn = HttpxConnection('http://127.0.0.1:8000/api/file')
conn.timeout = None
client = RpcClient('xbbg.blp', conn, async_local=False)
client.cache_get = True
client.cache_expire = 86400

blp = client
# 直接调用blpapi过于复杂，所以常使用基于此的一个封装包
# pip install blpapi --index-url=https://bcms.bloomberg.com/pip/simple/
# pip install xbbg

# 这两句直接替换即可
# from xbbg import blp
blp = client

# https://xbbg.readthedocs.io/en/latest/#features

df = blp.bdp(tickers='NVDA US Equity', flds=['Security_Name', 'GICS_Sector_Name'])
print(df)

df = blp.bdp('AAPL US Equity', 'Eqy_Weighted_Avg_Px', VWAP_Dt='20181224')
print(df)

df = blp.bdh(tickers='SPX Index', flds=['High', 'Low', 'Last_Price'], start_date='2018-10-10', end_date='2018-10-20')
print(df)
