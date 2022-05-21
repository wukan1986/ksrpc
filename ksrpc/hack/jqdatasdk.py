"""
jqdatasdk客户端替换
1. 将底层的instance替换成RpcClient。实现数据库相关的操作也能操作
"""


def hack(client):
    # 内部类就可以了，不用暴露出去
    class HackClient:
        def __init__(self, c):
            self.client = c
            self.not_auth = False

        def __getattr__(self, item):
            return self.client.__getattr__(item)

        def __call__(self, *args, **kwargs):
            return self

        def _reset(self):
            pass

        def ensure_auth(self):
            pass

        def logout(self):
            pass

    # 最简洁的用法，直接将最低层取数据的部分替换
    import jqdatasdk.client
    jqdatasdk.client.JQDataClient.instance = HackClient(client)
