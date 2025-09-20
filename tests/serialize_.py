import time

from ksrpc.serializer.pkl_gzip import serialize1, serialize
from ksrpc.server.demo import create_1d_array

aa = create_1d_array(200)
t1 = time.perf_counter()
a1 = serialize1(aa)
t2 = time.perf_counter()
a2 = serialize(aa)
t3 = time.perf_counter()
print(t2 - t1, t3 - t2)
print(len(a1), len(a2))
