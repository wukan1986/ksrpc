import sys
from typing import List

from loguru import logger

from ksrpc.connections import BaseConnection

__all__ = ['RpcClient', 'rpc_iterator', "Self"]


# 跨python版本导致反序列化失败，所以自己定义一个
# from typing_extensions import Self
class _Self:
    def __repr__(self):
        return "Self"


Self = _Self()


class RpcCall:

    def __init__(self, name, args, kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        if self.args is None:
            return self.name

        args = [f"{a}" for a in self.args]
        kwargs = [f"{k}={v}" for k, v in self.kwargs.items()]
        return f"{self.name}({','.join(args + kwargs)})"


class RpcClient:
    """
    RpcClient根据调用生成网络请求

    Notes
    -----
    __hash__ __module__ __class__ __dict__ __dir__ 与调试有关，所以请使用__getattr__('__hash__')等代替
    __str__ __repr__ 断点时RuntimeWarning，所以也使用__getattr__('__repr__')等代替

    """

    def __init__(self,
                 module: str,
                 connection: BaseConnection,
                 ref_id: id = 0,
                 calls: List[RpcCall] = [],
                 last_call: RpcCall = None,
                 lazy: bool = False,
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
        calls: List[RpcCall]
            前几步的方法列表
        lazy: bool
            - True - lazy: 遇到`()`不触发远程，而是到最后一步`collect_async()`。可以编写更复杂的语句
            - False - eager: 遇到`()`立即触发远程，所以`()`后的语句都是本地操作
        """
        self._module = module
        self._connection = connection
        self._ref_id = ref_id
        self._calls = calls
        self._last_call = last_call
        self._lazy = lazy

    def __del__(self):
        self._connection = None
        self._calls = None

    def __getattr__(self, name):
        # 注意：每次都生成新对象
        last_call = RpcCall(name, None, None)
        return RpcClient(self._module, self._connection, self._ref_id, self._calls + [last_call], last_call, self._lazy)

    def __call__(self, *args, **kwargs):
        self._last_call.args = args
        self._last_call.kwargs = dict(sorted(kwargs.items()))
        if self._lazy:
            return self
        else:
            return self.___call___()

    async def ___call___(self):
        is_server_raise = False
        data = None
        try:
            rsp = await self._connection.call(self._module, self._calls, self._ref_id)
            ref_id = rsp['ref_id']
            data = rsp['data']
            if rsp['status'] != 200:
                # 报异常，可用于迭代器等。这是服务端异常，不用走连接重置
                is_server_raise = True
                # 迭代器异常可以不打印，显示太多了
                if not isinstance(data, (StopAsyncIteration, StopIteration)):
                    print("Server Side Traceback",
                          "=====================",
                          rsp['traceback'], sep="\n", file=sys.stdout)
                # 抛出异常
                raise data
            if ref_id != 0:
                return RpcClient(self._module, self._connection, ref_id, rsp['calls'], None, self._lazy)
            return data
        except Exception as e:
            if is_server_raise:
                # 迭代器异常可以不打印，显示太多了
                if not isinstance(data, (StopAsyncIteration, StopIteration)):
                    logger.warning(f'{self._module}:{self._calls}, server error, {repr(e)}')
                raise
            else:
                # 本地异常，需重置
                await self._connection.reset()  # 重置
                logger.warning(f'{self._module}:{self._calls}, local error, {repr(e)}')
                raise

    def collect_async(self):
        """异步获取结果"""
        return self.___call___()

    def generate_stub(self):
        """生成对应模块的存根文件"""
        # output_file_path没有实际用途
        return self.__getattr__("generate_stub")(output_file_path=self._module)

    def __getitem__(self, item):
        # 语法糖，让RpcClient支持[]
        return self.__getattr__("__getitem__")(item)

    def __next__(self):
        return self.__getattr__("__next__")()

    async def __anext__(self):
        return self.__getattr__("__anext__")()

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

    def __getstate__(self):
        return {'module': self._module, 'calls': self._calls}

    def __setstate__(self, state):
        self._module = state['module']
        self._calls = state['calls']

    def __repr__(self):
        return f'<RpcClient[{self._module}:{self._calls}] at {id(self):#016x}>'


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
    if isinstance(generator, RpcClient):
        async for it in await generator.collect_async():
            try:
                yield await it.collect_async()
            except (StopAsyncIteration, StopIteration):
                break
    else:
        async for it in await generator:
            try:
                yield await it
            except (StopAsyncIteration, StopIteration):
                break
