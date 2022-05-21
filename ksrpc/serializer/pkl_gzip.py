#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author     :wukan
# @License    :(C) Copyright 2022, wukan
# @Date       :2022-05-05

"""
默认的系统内序列化与反序列化
1. 使用内置的pickle进行序列化与反序列化。无法跨语言
2. 使用gzip进行压缩

为了能完整的还原数据，在python语言的客户端中都使用pickle进行序列化
在跨语言的环境中，请使用json等更通用的格式
"""

import gzip
import pickle
from io import BytesIO


# !!! module序列化时会导致系统崩溃，所以不使用dill
# import dill as pickle


def serialize(obj):
    """序列化

    !!! 注意：部分对象无法序列化
    """
    b1 = BytesIO()
    pickle.dump(obj, b1)
    b1.seek(0)
    b2 = BytesIO(gzip.compress(b1.read()))
    return b2


def deserialize(buf):
    """反序列化"""
    b1 = gzip.decompress(buf)
    b2 = BytesIO(b1)
    bb = pickle.load(b2)
    return bb
