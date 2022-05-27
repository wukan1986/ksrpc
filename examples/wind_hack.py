# 创建客户连接
from ksrpc import RpcClient
from ksrpc.connections.http import HttpxConnection
from ksrpc.hack.WindPy import hack

conn = HttpxConnection('http://127.0.0.1:8000/api/file')
conn.timeout = None
client = RpcClient('WindPy', conn, async_local=False)
client.cache_get = True
client.cache_expire = 86400

# 对原版库进行定制处理，需要已经安装了原版库
hack(client)

from WindPy import w

w.start()

error, data = w.wsd("510050.SH", "close", "2021-09-01", "2021-09-23", "", usedf=True)
print(error)
print(data)
