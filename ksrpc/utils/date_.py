#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author     :wukan
# @License    :(C) Copyright 2022, wukan
# @Date       :2022-03-02

"""
API输入时间参数过于动态不利于缓存key生成

例如date.now()时间一直在变化，如果转成日期或转成周五，可以大量减少key
"""

from datetime import datetime

import numpy as np
import pandas as pd


def to_date_str(dt):
    """只取日期部分"""
    if isinstance(dt, int):
        dt = str(dt)
    if isinstance(dt, str):
        if ':' in dt:
            return dt[:10]
        if len(dt) == 10:
            return dt
    if isinstance(dt, (str, np.datetime64)):
        dt = pd.to_datetime(dt)
    return f'{dt:%Y-%m-%d}'


def eq_today(end_date):
    """等于今天"""
    return to_date_str(end_date) == f'{datetime.today():%Y-%m-%d}'


def ge_today(end_date):
    """大于等于今天"""
    return to_date_str(end_date) >= f'{datetime.today():%Y-%m-%d}'


if __name__ == '__main__':
    print(eq_today(20210925))
    print(eq_today(20210929))
    print(to_date_str(20210925))
    print(to_date_str('2021-09-25 01:44:29.477371'))
    print(to_date_str('2021-09-25T01:44:29.477371'))
    print(eq_today('2021-09-29T01:44:29.477371'))
    print(eq_today('2021-09-30'))
    print(ge_today('2021-09-30'))
    print(to_date_str(datetime.now()))
    print(to_date_str(datetime.now().date()))
    print(to_date_str(pd.to_datetime(datetime.now())))
    print(to_date_str(np.datetime64(datetime.now())))

    from dateutil.relativedelta import relativedelta, FR

    print(datetime(2021, 9, 25) + relativedelta(weekday=FR(-1)))
    print(datetime(2021, 9, 25) + relativedelta(weekday=FR(0)))
    print(datetime(2021, 9, 25) + relativedelta(weekday=FR(+1)))
