import asyncio

from ksrpc.caller import is_import_allowed, get_calls
from ksrpc.client import RpcCall, Self

IMPORT_RULES = {
    "ksrpc*": True,
    "*": False,
}

IMPORT_RULES = {
    "ksrpc.*": True,
    "*": False,
}

IMPORT_RULES = {
    "ksrpc.*.demo": True,
    "*": False,
}

IMPORT_RULES = {
    "*.demo": True,
    "*": False,
}


async def main():
    print(is_import_allowed("ksrpc.server.demo", IMPORT_RULES))
    print(is_import_allowed("ksrpc.server", IMPORT_RULES))
    print(is_import_allowed("ksrpc", IMPORT_RULES))

    c1 = RpcCall('demo', None, None)
    c2 = RpcCall('__call__', (), {})
    out = await get_calls("ksrpc.server", [c1, c2], 0)
    print(out)

    c1 = RpcCall('demo', None, None)
    c2 = RpcCall('open', (Self,), {})
    out = await get_calls("ksrpc.server", [c1, c2], 0)
    print(out)

    c0 = RpcCall("server", None, None)
    c1 = RpcCall('demo', None, None)
    c2 = RpcCall('test', (), {})
    out = await get_calls("ksrpc.server", [c1, c2], 0)
    print(out)
    out = await get_calls("ksrpc", [c0, c1, c2], 0)
    print(out)

    c1 = RpcCall('globals', (), {})
    c2 = RpcCall('__getitem__', ("__name__",), {})
    out = await get_calls("builtins", [c1, c2], 0)
    print(out)


asyncio.run(main())
