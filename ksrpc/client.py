from typing import List

from loguru import logger

from ksrpc.connections import BaseConnection

__all__ = ['RpcClient', 'rpc_iterator']


class RpcClient:
    """
    RpcClient根据调用生成网络请求。
    不建议用户直接使用，请用RpcProxy

    Warnings
    --------
    先调用一到多个`__getattr__`，然后`__call__`收集`__getattr__`的结果。
    并行时`__getattr__`的调用先后不可控，所以不能在`asyncio.gather`中使用

    Notes
    -----
    __hash__ __module__ __class__ __dict__ __dir__ 与调试有关，所以请使用__getattr__('__hash__')等代替
    __str__ __repr__ 断点时RuntimeWarning，所以也使用__getattr__('__repr__')等代替

    """

    def __init__(self,
                 module: str,
                 connection: BaseConnection,
                 ref_id: id = 0,
                 reraise: bool = True,
                 names: List[str] = []
                 ):
        """初始化

        Parameters
        ----------
        module: str
            顶层模块名
        connection: Connection
            连接对象
        ref_id: int
            服务端的对象id。用于迭代器，生成器等
        reraise: bool
            重新抛出服务端异常，而不是返回字典
        names: List[str]
            前几步的方法列表
        """
        self._module = module
        self._connection = connection
        self._ref_id = ref_id
        self._reraise = reraise
        self._names = names

    def __del__(self):
        self._connection = None
        self._names = None

    def __getattr__(self, name):
        # 注意：每次都生成新对象
        return RpcClient(self._module, self._connection, self._ref_id, self._reraise, self._names + [name])

    async def __call__(self, *args, **kwargs):
        name = '.'.join(self._names)
        # print("__call__", name)
        # 排序，参数顺序统一后，排序生成key便不会浪费了
        kwargs = dict(sorted(kwargs.items()))
        is_server_raise = False
        try:
            rsp = await self._connection.call(self._module, name, args, kwargs, self._ref_id)
            ref_id = rsp['ref_id']
            if rsp['status'] != 200:
                is_server_raise = True
                if self._reraise:
                    # 报异常，可用于迭代器等。这是服务端异常，不用走连接重置
                    raise rsp['data']
                else:
                    # 直接反回错误字典，不会报异常
                    return rsp
            if ref_id != 0:
                return RpcClient(self._module, self._connection, ref_id, self._reraise, [rsp['name']])
            return rsp['data']
        except Exception as e:
            # 服务端异常，直接抛出
            if is_server_raise:
                logger.warning(f'{self._module}::{name}, server error, {repr(e)}')
                raise
            # 本地异常，需重置
            await self._connection.reset()  # 重置
            logger.warning(f'{self._module}::{name}, local error, {repr(e)}')
            raise

    def __getitem__(self, item):
        # 语法糖，让RpcClient支持[]
        return self.__getattr__("__getitem__")(item)

    # @property
    # def __doc__(self):
    #     return self.__getattr__('__doc__')

    @property
    def __format__(self, format_spe: str = ""):
        # 这里""不能省
        return self.__getattr__('__format__')

    def __next__(self):
        return self.__getattr__("__next__")

    async def __anext__(self):
        return self.__getattr__("__anext__")

    def __iter__(self):
        # 本项目全是异步，理论上本句不会被调用
        # return self.__getattr__("__iter__")
        return self

    def __aiter__(self):
        # ksrpc.server.demo::async_counter.__aiter__.__anext__
        # return self.__getattr__("__aiter__")

        # TODO 取巧办法，等更好方案
        # ksrpc.server.demo::async_counter.__anext__
        return self


async def rpc_iterator(generator):
    """封装远程的迭代器。远程的异步和同步迭代器，都统一成异步

    Parameters
    ----------
    generator

    Examples
    --------
    ```python
    # 一定要抛出异常，否则
    demo = RpcProxy('ksrpc.server.demo', conn, reraise=True)

    async for it in rpc_iterator(demo.async_counter()):
        print(it)

    async for it in rpc_iterator(demo.sync_counter()):
        print(it)
    ```

    """
    async for it in await generator:
        try:
            yield await it()
        except (StopAsyncIteration, StopIteration):
            break
