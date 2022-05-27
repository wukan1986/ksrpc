from ksrpc import RpcClient
from ksrpc.connections.http import HttpxConnection

conn = HttpxConnection('http://127.0.0.1:8000/api/file')
conn.timeout = None
math = RpcClient('math', conn, async_local=False)
math.cache_get = True
math.cache_expire = 86400

# 模块中变量获取方法。这里加了括号
print(math.pi())

print(math.pow(2, 3))
print(math.pow.__call__(2, 3))
