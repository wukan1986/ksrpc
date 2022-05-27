from ksrpc import RpcClient
from ksrpc.connections.http import HttpxConnection

conn = HttpxConnection('http://127.0.0.1:8000/api/file')
conn.timeout = None
pd = RpcClient('pandas', conn, async_local=False)
pd.cache_get = True
pd.cache_expire = 86400

# 注意这是服务器上文件的路径
df = pd.read_csv('../tests/20210104.csv')
print(df)

df = pd.util.testing.makeTimeDataFrame()
print(df)

# 其实与上面是传的参数是完全一样的
testing = RpcClient('pandas.util.testing', conn, async_local=False)
df = testing.makeTimeDataFrame()
print(df)


