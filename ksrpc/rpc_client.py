# 客户端，用于处理请求
# 需要选择到底是http还是ws，还是nng一类的
import asyncio

from loguru import logger
from revolving_asyncio import to_async, to_sync


class RpcClient:
    """是否优先从缓存中获取"""
    cache_get: bool = True
    """缓存超时时间，秒"""
    cache_expire: int = 86400
    """本地是否暴露为异步，async def函数中才能启用"""
    async_local = False
    """远程是否以异步方式掉用，某些情况下设置成同步才不报错"""
    async_remote = True
    """接收超时时间，秒"""
    recv_timeout = 30

    def __init__(self,
                 module,
                 connection,
                 async_local=False,
                 async_remote=True,
                 ):
        """初始化

        Parameters
        ----------
        module: str
            模块名
        connection: Connection
            连接对象
        async_local: bool
            是否暴露为异步调用，async def函数中才能启用
        async_remote: bool
            远程是否以异步方式掉用，某些情况下设置成同步才不报错
        """
        self._connection = connection
        self._module = module
        self._methods = [module]
        self.async_local = async_local
        self.async_remote = async_remote

    def __getattr__(self, method):
        self._methods.append(method)
        return self

    def __call__(self, *args, **kwargs):
        # 排序，参数顺序统一后，排序生成key便不会浪费了
        kwargs = dict(sorted(kwargs.items()))

        func = '.'.join(self._methods)
        # 用完后得重置，否则第二次用时不正确了
        self._methods = [self._module]
        # 指定外部调用方式是同步还是异步
        if self.async_local:
            f = to_async(self._connection.call)
        else:
            f = to_sync(self._connection.call)

        try:
            # 注意：这里没有指定输入输出格式，只有输入二进制，输出二进制的格式
            # 服务器可以支持多种格式是用于非python客户端
            return f(func, args, kwargs,
                     cache_get=self.cache_get, cache_expire=self.cache_expire, async_remote=self.async_remote,
                     timeout=self.recv_timeout)
        except asyncio.TimeoutError:
            self._connection._with = False  # 重置
            logger.warning(f'{func} timeout, {self.recv_timeout}s')
            raise
        except Exception as e:
            self._connection._with = False  # 重置
            logger.warning(f'{func} error, {e}')
            raise

    def __len__(self):
        # 不知怎么回事，被主动调用了
        return 0
