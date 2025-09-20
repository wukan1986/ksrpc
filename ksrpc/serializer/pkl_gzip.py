"""
默认的系统内序列化与反序列化
1. 使用内置的pickle进行序列化与反序列化。无法跨语言
2. 使用zlib进行压缩

为了能完整的还原数据，在python语言的客户端中都使用pickle进行序列化
在跨语言的环境中，请使用json等更通用的格式

HTTP中使用序列化后再整体压缩
WebSocket使用序列化后分片压缩
"""

import pickle
import zlib


def serialize(obj, compression_level=6):
    # 使用 zlib 压缩
    return zlib.compress(pickle.dumps(obj), level=compression_level)


def deserialize(compressed_data):
    # 反序列化对象
    return pickle.loads(zlib.decompress(compressed_data))
