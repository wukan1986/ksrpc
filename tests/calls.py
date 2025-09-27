import asyncio

from ksrpc.caller import get_calls
from ksrpc.client import RpcCall


async def main():
    c0 = RpcCall("server", None, None)
    c1 = RpcCall('demo', None, None)
    c2 = RpcCall('test', (), {})
    out = await get_calls("ksrpc.server", [c1, c2])
    print(out)
    out = await get_calls("ksrpc", [c0, c1, c2])
    print(out)

    c1 = RpcCall('globals', (), {})
    c2 = RpcCall('__getitem__', ("__name__",), {})
    out = await get_calls("builtins", [c1, c2])
    print(out)


asyncio.run(main())
