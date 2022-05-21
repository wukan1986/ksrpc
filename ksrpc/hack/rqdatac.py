"""
rqdatac客户端替换
1. 将底层的rqdatac.client替换成RpcClient
2. init替换，防止登陆
"""


def hack(client):
    # 内部类就可以了，不用暴露出去
    class HackClient:
        PID = -1

        def __init__(self, c):
            self.client = c

        def execute(self, *args, **kwargs):
            return self.client.execute(*args, **kwargs)

        def reset(self):
            pass

        def info(self):
            pass

        def close(self):
            pass

    def __init(username=None, password=None, addr=("rqdatad-pro.ricequant.com", 16011), *_, **kwargs):
        pass

    # 最简洁的用法，直接将最低层取数据的部分替换
    import rqdatac.client
    rqdatac.client._CLIENT = HackClient(client)
    rqdatac.client.init = __init
    import rqdatac
    rqdatac.init = __init
