# ksrpc

Keep Simple RPC。免注册远程过程调用

!!! 注意：已经迭代成第二代。第一代请参考[fastapi](https://github.com/wukan1986/ksrpc/tree/fastapi)分支

## 安全

注意：第二代只有`Baisc认证`和`导入规则列表`，其它功能无任何限制，甚至可以执行`rm -rf /`。所以强烈建议

1. 账号只给少量可信之人
2. 只部署在docker中
3. 服务不用时最好停止，或定时任务启停
4. 不要使用默认端口、默认账号、默认URL路径等
5. 导入规则列表最后一条建议`"*": False`

## 第二代 vs 第一代

### 第一代

1. 功能比较多：IP黑白名单、函数黑白名单、内网反代、数据缓存、跨语言多数据格式
2. 实际考察发现，只有内网反代功能才是大家需要的，其他功能都极少有人用
3. 缺点：由于当初没有在数据包中加入请求编号或会话编号，多人都挤同房间数据会混乱
4. pip install ksrpc<0.6.0

### 第二代

1. 考虑到大家只关注内网反代，所以决定用更专业的反代工具，如：`frp`等
2. 删减功能，只留`API`调用+`Baisc`认证+`导入规则列表`
3. 某平台中的`FastAPI`所创建的服务只要访问，`uvicorn`就崩溃，最后决定将客服端和服务端都替换成`aiohttp`
4. `async`和`sync`的互转导致系统非常混乱，清理只留`async`。但所有不改代码的`hack`功能作废
5. pip install ksrpc>=0.6.0

## 安装

```bash
pip install ksrpc -i https://mirrors.aliyun.com/pypi/simple --upgrade
# 或
pip install ksrpc -i https://pypi.org/simple --upgrade
```

## 使用

1. 服务端

```bash
# 直接运行
python -m ksrpc.run_app
# 使用配置运行
python -m ksrpc.run_app --config ./config.py
```

2. 客户端

```python
import asyncio

from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection

# 动态URL
URL = 'http://127.0.0.1:8080/api/v1/{time}'
USERNAME = 'admin'
PASSWORD = 'password123'


async def async_main():
    async with HttpConnection(URL, username=USERNAME, password=PASSWORD) as conn:
        demo = RpcClient('ksrpc.server.demo', conn)

        print(await demo.test())


asyncio.run(async_main())
```

## 远程调用规则

```python
# eager模式
RpcClient(..., lazy=False)
await 一个模块.零到多个模块或方法或属性.一个方法或属性(参数)
# lazy模式
RpcClient(..., lazy=True)
await 一个模块.零到多个模块或方法或属性.一个方法或属性(参数).一个方法或属性(参数).collect_async()
```

### eager模式

1. 语句后接`()`就会触发远程调用
2. `.`后的函数用来收集调用链
3. `[]`本质是`.__getitem__(item)`,内部会调整成`.__getattr__("__getitem__").__call__(item)`，会立即触发远程调用
4. 大部分情况用户代码只在最后出现`()`或`[]`，`eager`模式已经够用

### lazy模式

1. 语句后接`collect_async()`就会触发远程调用
2. `.`后的函数用来收集调用链，`()`用来收集参数
3. `[]`本质同`eager`模式，但触发要等`collect_async()`
4. 只要语句中间出现`()`或`[]`，`lazy`模式才能处理

### lazy模式特别语法

部分语句还是非常难实现

1. `__getattr__('__str__')()` # 一般都存在，就算不存在也会退回到`__repr__`
2. `__getattr__('__int__')()` # 自定义对象有可能实现，而`str`没有`__int__`

所以专门提供了一种特殊语法`.func(Self)`，它能成功运行依赖于3个条件：

1. `from ksrpc.client import Self`，然后传入`Self`参数
2. `builtins`中已经定义了`func`函数
3. `config.py`中`IMPORT_RULES`已经设置了`"builtins": True`，或没有设置`builtins`, 但设置了`"*": True`

前面两句可以简化成

1. `str(Self)`
2. `int(Self)`

建议先写原始代码测试通过，然后改成魔术方法版测试通过，最后才是远程异步版。例如：

```python
from ksrpc.client import RpcClient, Self
from ksrpc.server import demo

print(len(demo.__file__))  # 1. 在服务端或本地测试是否通过
print(demo.__file__.__len__())  # 2. 翻译成魔术方法版。看是否正常

demo1 = RpcClient('ksrpc.server.demo', conn)
demo2 = RpcClient('ksrpc.server.demo', conn, lazy=True)
print(await demo1.__file__.__len__())  # 3. 改成远程异步版。网络中传输的是`int`
print((await demo1.__file__()).__len__())  # 得到结果一样，但网络中传输的是`str`，然后本地算的`len()`
print(await demo2.__file__.__len__().collect_async())  # lazy模式，collect_async()前的代码都会在服务端计算
print(await demo2.__file__.len(Self).collect_async())  # lazy模式下的Self扩展写法

print(demo1.__doc__)  # 取的其实是RpcClient的__doc__
print(await demo1.__getattr__('__doc__')())  # 取的远程ksrpc.server.demo.__doc__
```

更多调用方式参考[examples](https://github.com/wukan1986/ksrpc/blob/main/examples)

## 工作原理

1. 创建`Web`服务，接收请求后，调用服务器中的`Python`库，将结果二进制封装后返回
2. 客户端将`API`调用封装，然后向`Web`服务器请求，等待返回
3. 返回结果解包成`Python`对象
4. 反代时`frp`需要公网有服务器进行转发。当然你也可以使用其他组网工具，如`easytier`等

内网反代参考[examples_frp](https://github.com/wukan1986/ksrpc/tree/main/examples_frp)

## 传输方式

1. 先整体`zlib`压缩，然后分`chunk`传输
    - 由于整体压缩，所以可以用第三方软件直接解压
    - 浏览器和其他工具能直接识别'Content-Encoding': 'deflate'并解压
2. 先分`chunk`，每个`chunk`都分别使用`zlib`压缩再传输
    - 分块压缩，只能分块解压。第三方工具失效
    - 将大文件压缩耗时分拆了，速度显著提升

本项目的`HTTP`和`WebSocket`都使用了方案二，先分`chunk`后`zlib`压缩

## 参考项目

开发到一定阶段后才发现与`rpyc`这个免注册暴露函数的功能类似，大家也可以去学习一下

https://github.com/tomerfiliba-org/rpyc

## 声明

此库仅供学习交流，请在数据提供方的授权范围内使用。请勿向第三方转发数据