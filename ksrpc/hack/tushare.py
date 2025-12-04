"""
TuShare客户端替换
1. 将TuShare底层的pro替换成RpcClient
2. set_token和pro_api还是使用的客户本地API
"""


def hack(client):
    # 最简洁的用法，直接将最低层取数据的部分替换
    def __pro_api(token='', timeout=30):
        return client

    import tushare
    tushare.pro_api = __pro_api
