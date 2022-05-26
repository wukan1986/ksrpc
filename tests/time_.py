from ksrpc import RpcClient
from ksrpc.connections.http import HttpxConnection

conn = HttpxConnection('http://127.0.0.1:8000/api/file')
conn.timeout = None
time = RpcClient('time', conn, is_async=False)
time.cache_get = True
time.cache_expire = 86400

ret = time.sleep(5)
print(ret)
ret = time.sleep.__call__(1)
print(ret)
