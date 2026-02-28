# 官方测试代码
import os

import tushare as ts

pro = ts.pro_api(token=os.getenv("TUSHARE_TOKEN"), timeout=30)

df = pro.daily(ts_code='000001.SZ', start_date='20180701', end_date='20180718')

print(df)
