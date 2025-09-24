import asyncio
import threading

from loguru import logger

from ksrpc.connections import BaseConnection


class RpcClient:
    """
    RpcClient根据调用生成网络请求

    Warnings
    --------
    先调用一到多个`__getattr__`，然后`__call__`收集`__getattr__`的结果。
    并行时`__getattr__`的调用先后不可控，所以不能在`asyncio.gather`中使用

    """

    def __init__(self,
                 module: str,
                 connection: BaseConnection,
                 ref_id: id = 0,
                 ):
        """初始化

        Parameters
        ----------
        module: str
            顶层模块名
        connection: Connection
            连接对象
        ref_id:
            服务端的对象id。用于迭代器，生成器等

        """
        self._module = module
        self._connection = connection
        self._ref_id = ref_id
        self._names = []
        self._lock = threading.Lock()

    def __del__(self):
        self._connection = None

    def __getattr__(self, name):
        with self._lock:
            # 同一对象在asyncio.gather中使用会混乱，请用独立对象
            self._names.append(name)
            return self

    async def __call__(self, *args, **kwargs):

        with self._lock:
            name = '.'.join(self._names)
            # 用完后得重置，否则第二次用时不正确了
            self._names = []
        # print("__call__", name)
        # 排序，参数顺序统一后，排序生成key便不会浪费了
        kwargs = dict(sorted(kwargs.items()))
        try:
            rsp = await self._connection.call(self._module, name, args, kwargs, self._ref_id)
            ref_id = rsp['ref_id']
            if rsp['status'] != 200:
                # 迭代器可能用它来停止，但效果不行
                # raise rsp['data']
                # 直接反回错误字典，不会报异常
                return rsp
            if ref_id != 0:
                return RpcClient(self._module, self._connection, ref_id=ref_id)
            return rsp['data']
        except asyncio.TimeoutError:
            await self._connection.reset()  # 重置
            logger.warning(f'{self._module}::{name} timeout')
            raise
        except Exception as e:
            await self._connection.reset()  # 重置
            logger.warning(f'{self._module}::{name} error, {e}')
            raise

    def __getitem__(self, item):
        # 语法糖，让RpcClient支持[]
        return self.__getattr__("__getitem__")(item)

    @property
    def __class__(self):
        return self.__getattr__('__class__')

    @property
    def __dict__(self):
        return self.__getattr__('__dict__')

    @property
    def __dir__(self):
        return self.__getattr__('__dir__')

    @property
    def __doc__(self):
        return self.__getattr__('__doc__')

    @property
    def __format__(self, format_spe: str = ""):
        # 这里=""不能省
        return self.__getattr__('__format__')

    @property
    def __hash__(self):
        return self.__getattr__('__hash__')

    @property
    def __module__(self):
        return self.__getattr__('__module__')

    @property
    def __repr__(self):
        return self.__getattr__('__repr__')

    @property
    def __sizeof__(self):
        return self.__getattr__('__sizeof__')

    @property
    def __str__(self):
        return self.__getattr__('__str__')

    # === 生成器和迭代器都有问题，不要用
    def __next__(self):
        # TODO 这里为何还要加一个()才可以？与我的理解不同呀
        print("__next__")
        return self.__getattr__("__next__")()

    async def __anext__(self):
        # 特殊之处，需要传对象id
        print("__anext__")
        return self.__getattr__("__anext__")()

    def __iter__(self):
        print("__iter__")
        return self.__getattr__("__iter__")

    def __aiter__(self):
        print("__aiter__")
        return self


class RpcProxy(RpcClient):
    """每次调用都生成一个`RpcClient`对象，占用资源略多于`RpcClient`

    Notes
    --------
    `__getattr__`后就已经是一个独立的`RpcClient`对象，可以在`asyncio.gather`中并行使用

    """

    def __getattr__(self, name):
        # 第一个方法调用用来生成新RpcClient对象，用来解决不能并发的问题
        return RpcClient(self._module, self._connection, self._ref_id).__getattr__(name)

    async def __call__(self, *args, **kwargs):
        return await RpcClient(self._module, self._connection, self._ref_id)()

    @property
    def __doc__(self):
        # 比较特殊
        return self.__getattr__('__doc__')
