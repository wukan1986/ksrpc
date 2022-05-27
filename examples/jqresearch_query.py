# 此文件需复制到被控端, 当前前工作目录下，如Notebook同目录等
# jqresearch.api.get_fundamentals
# 只能以同步方式调用
def get_fundamentals_valuation(date):
    q = query(
        valuation
    )
    df = get_fundamentals(q, date)
    return df
