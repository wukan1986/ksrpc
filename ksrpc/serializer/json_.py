#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author     :wukan
# @License    :(C) Copyright 2022, wukan
# @Date       :2022-05-02

"""
特殊设计的json互转
1. DataFrame和Series的解析最好能在信息完整与空间大小之间平衡，所以选择tight模式
    1. to_dict有tight模式，而to_json却没有
2. 时间希望能正确的转为字符串。pandas._libs.json能正确解析时间

"""
import copy

import numpy as np
import pandas as pd
# 不使用内置json是为了方便处理时间格式
import pandas._libs.json as json


def obj_to_dict(obj):
    """将pandas转成字典，方便后期转成json格式"""
    if isinstance(obj, pd.DataFrame):
        d = obj.to_dict(orient='tight')
    elif isinstance(obj, pd.Series):
        d = obj.to_dict()
    else:
        # 复制一下，防止后期修改了原数据
        if hasattr(obj, 'copy'):
            d = obj.copy()
        else:
            d = copy.copy(obj)
    return d


def dict_to_json(d: dict):
    """字典转json

    调用import pandas._libs.json as json来进行转换，解决时间格式转换问题
    """
    # 复合索引的元组可能简单的只拼接成字符串，导致无法还原
    return json.dumps(d, iso_dates=True)


def json_to_dict(text):
    """json转字典

    调用import pandas._libs.json as json来进行转换，解决时间格式转换问题
    """
    return json.loads(text)


def dict_to_obj(d):
    """dict转pandas"""
    # ndarray直接返回即可
    if isinstance(d, np.ndarray):
        return d
    # list可以转成一维或二维ndarray
    if isinstance(d, list):
        return np.array(d)
    if isinstance(d, dict):
        if 'data' in d:
            # 与to_dict参数对应
            return pd.DataFrame.from_dict(d, orient='tight')
        else:
            # 丢失了index上的name
            return pd.Series(d)


def _display(o1):
    """显示测试"""
    print('=' * 100)
    d1 = obj_to_dict(o1)
    print('-' * 60, 'pandas转dict')
    print(d1)
    j1 = dict_to_json(d1)
    print('-' * 60, 'dict转json')
    print(j1)
    print('-' * 60, 'dict转object')
    print(dict_to_obj(d1))
    d2 = json_to_dict(j1)
    print('-' * 60, 'json转dict')
    print(d2)
    o2 = dict_to_obj(d2)
    print('-' * 60, 'dict转pandas')
    print(o2)


if __name__ == '__main__':
    MINUTES_PER_YEAR = 8
    NUMBER_OF_SHARES = 5

    pd._testing._N = MINUTES_PER_YEAR
    pd._testing._K = NUMBER_OF_SHARES  # 只会显示26个字母

    df = pd._testing.makeTimeDataFrame(freq="5min")
    # df = pd._testing.makeDataFrame()

    # 复合索引测试
    # df = df.set_index('A', append=True)

    _display(df.values)
    _display(df)
    _display(df['B'].values)
    _display(df['B'])
    print(df['B'].to_json())
