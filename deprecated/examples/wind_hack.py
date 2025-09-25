# 创建客户连接
from ksrpc.hack.WindPy import hack

from ksrpc.client import RpcProxy
from ksrpc.connections.http import HttpConnection

conn = HttpConnection('http://127.0.0.1:8000/api/file')
client = RpcProxy('WindPy', conn)

# 对原版库进行定制处理，需要已经安装了原版库
hack(client)

from WindPy import w

w.start()

error, data = w.wsd("510050.SH", "close", "2021-09-01", "2021-09-23", "", usedf=True)
print(error)
print(data)
