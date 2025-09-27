# 此文件需复制到服务端, 当前工作目录下，如Notebook同目录等
# jqresearch.api.get_fundamentals
def get_fundamentals_valuation(date):
    # q中含session无法序列化，但输入date和返回DataFrame都可以序列化，所以提供一个文件进行中转
    q = query(
        valuation
    )
    df = get_fundamentals(q, date)
    return df
