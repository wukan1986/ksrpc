# 客户端，用于处理请求
# 需要选择到底是http还是ws，还是nng一类的
import asyncio

from loguru import logger

from ksrpc.connections import BaseConnection


class RpcClient:
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
        self._lock = asyncio.Lock()

    def __getattr__(self, method):
        # TODO 同一对象在asyncio.gather中使用会混乱
        self._methods.append(method)
        return self

    def __len__(self):
        # 不知怎么回事，被主动调用了
        return 0

    async def __call__(self, *args, **kwargs):
        # 排序，参数顺序统一后，排序生成key便不会浪费了
        kwargs = dict(sorted(kwargs.items()))

        methods_str = '.'.join(self._methods)
        # 用完后得重置，否则第二次用时不正确了
        self._methods = []

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
