from ksrpc import RpcClient
from ksrpc.connections.http import HttpxConnection

conn = HttpxConnection('http://127.0.0.1:8000/api/file')
conn.timeout = None
ak = RpcClient('akshare', conn, async_local=False)
ak.cache_get = True
ak.cache_expire = 86400

df = ak.stock_zh_a_st_em()
print(df)
