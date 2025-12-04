"""
Wind客户端替换
1. 将底层的w替换成RpcClient
"""


def hack(client):
    import WindPy
    WindPy.w = client
