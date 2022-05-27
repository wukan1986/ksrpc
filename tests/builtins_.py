from ksrpc import RpcClient
from ksrpc.connections.http import HttpxConnection

conn = HttpxConnection('http://127.0.0.1:8000/api/file')
conn.timeout = None
builtins = RpcClient('builtins', conn, async_local=False)
builtins.cache_get = True
builtins.cache_expire = 86400

token = 'secret-token-2'

# 记算的结果取回来了
print(builtins.eval('2*3'))
# 打印在了服务器上
print(builtins.print('2*3'))
