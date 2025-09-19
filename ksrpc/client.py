# 客户端，用于处理请求
# 需要选择到底是http还是ws，还是nng一类的
import asyncio
import threading

from loguru import logger

from ksrpc.connections import BaseConnection


class RpcClient:
    """根据函数调用生成网络请求

    Warnings
    --------
    不能在`asyncio.gather`中使用
    """

    def __init__(self,
                 module: str,
                 connection: BaseConnection,
                 ):
        """初始化

        Parameters
        ----------
        module: str
            模块名
        connection: Connection
            连接对象

        """
        self._module = module
        self._connection = connection
        self._methods = []
        self._lock = threading.Lock()

    def __getattr__(self, method):
        with self._lock:
            # 同一对象在asyncio.gather中使用会混乱，请用独立对象
            self._methods.append(method)
            return self

    def __len__(self):
        # 不知怎么回事，被主动调用了
        return 0

    def __del__(self):
        self._connection = None

    async def __call__(self, *args, **kwargs):
        with self._lock:
            methods_str = '.'.join(self._methods)
            # 用完后得重置，否则第二次用时不正确了
            self._methods = []

        # 排序，参数顺序统一后，排序生成key便不会浪费了
        kwargs = dict(sorted(kwargs.items()))
        try:
            return await self._connection.call(self._module, methods_str, args, kwargs)
        except asyncio.TimeoutError:
            await self._connection.reset()  # 重置
            logger.warning(f'{self._module}::{methods_str} timeout')
            raise
        except Exception as e:
            await self._connection.reset()  # 重置
            logger.warning(f'{self._module}::{methods_str} error, {e}')
            raise


class RpcProxy:
    """每次调用都生成一个RpcClient对象，占用资源略多于RpcClient

    Notes
    --------
    可以在`asyncio.gather`中并行使用

    """

    def __init__(self,
                 module: str,
                 connection: BaseConnection,
                 ):
        """初始化

        Parameters
        ----------
        module: str
            模块名
        connection: Connection
            连接对象
        """
        self._module = module
        self._connection = connection

    def __getattr__(self, method):
        # 第一个方法调用用来生成新RpcClient对象，用来解决不能并发的问题
        return RpcClient(self._module, self._connection).__getattr__(method)

    def __del__(self):
        self._connection = None
