# 此文件需复制到被控端, 当前前工作目录下，如Notebook同目录等
# jqresearch.api.get_fundamentals
# 只能以同步方式调用
import pandas as pd

from jqresearch.api import *  # noqa


def get_fundamentals_balance(date=None, statDate=None):
    """资产负债数据，按季更新"""
    q = query(
        balance
    )
    return get_fundamentals(q, date=date, statDate=statDate)


def get_fundamentals_cash_flow(date=None, statDate=None):
    """现金流数据，按季更新，单季"""
    q = query(
        cash_flow
    )
    return get_fundamentals(q, date=date, statDate=statDate)


def get_fundamentals_income(date=None, statDate=None):
    """利润数据，按季更新，单季"""
    q = query(
        income
    )
    return get_fundamentals(q, date=date, statDate=statDate)


def get_fundamentals_indicator(date=None, statDate=None):
    """财务指标数据，按季更新，单季"""
    q = query(
        indicator
    )
    return get_fundamentals(q, date=date, statDate=statDate)


def get_fundamentals_valuation(date=None, statDate=None):
    """市值数据，每日更新"""
    dfs = []
    last_id = -1
    while True:
        q = (
            query(valuation)
            .filter(valuation.id > last_id)
            .order_by(valuation.id)
            .limit(4000)
        )

        df = get_fundamentals(q, date=date, statDate=statDate)
        if df.empty:
            break
        last_id = df['id'].iloc[-1]
        dfs.append(df)

    if len(dfs) == 0:
        return pd.DataFrame()
    else:
        return pd.concat(dfs).reset_index(drop=True)

