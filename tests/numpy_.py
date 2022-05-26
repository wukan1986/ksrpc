from ksrpc import RpcClient
from ksrpc.connections.http import HttpxConnection

conn = HttpxConnection('http://127.0.0.1:8000/api/file')
conn.timeout = None
np = RpcClient('numpy', conn, is_async=False)
np.cache_get = True
np.cache_expire = 86400

arr = np.array([1, 2, 3, 4, 5])
print(arr)
