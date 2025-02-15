# 创建客户连接
from ksrpc import RpcClient
from ksrpc.connections.http import HttpxConnection

conn = HttpxConnection('http://127.0.0.1:8000/api/file')
client = RpcClient('rqdatac', conn, async_local=False)
client.cache_get = True
client.cache_expire = 86400

print(client.RQ_USERNAME())

# 对原版库进行定制处理，需要已经安装了原版库
from ksrpc.hack.rqdatac import hack

hack(client)

# 原版代码可都保持不变
import rqdatac

rqdatac.init(username='RQ_USERNAME', password='RQ_PASSWORD')

df = rqdatac.get_price('IF88', start_date='2021-08-01', end_date='2021-08-10')
print(df)
