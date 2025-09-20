import ksrpc.server.demo

print(ksrpc.server.demo.test())
print(ksrpc.server.demo.PASSWORD)
print(ksrpc.server.demo.LIST.__getitem__(2))
print(ksrpc.server.demo.CLASS.D.C.__getitem__(3))

from ksrpc.caller import get_func

print(get_func('ksrpc', 'server.demo.CLASS.D.C.__getitem__'))
print(get_func('ksrpc.server', 'demo.CLASS.D.C.__getitem__'))
print(get_func('ksrpc.server.demo', 'CLASS.D.C.__getitem__'))
