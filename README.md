# ksrpc

Keep Simple RPC。免注册远程过程调用

!!! 注意：已经修剪成第二代。第一代请参考[fastapi](https://github.com/wukan1986/ksrpc/tree/fastapi)分支

## 安全

注意：第二代只有`Baisc`认证，其它功能无任何限制。所以强烈建议

1. 账号只给少量可信之人
2. 只部署在docker中
3. 服务不用时最好停止，或定时任务启停
4. 不要使用默认端口、默认账号、默认URL路径等

## 第二代 vs 第一代

### 第一代

1. 功能比较多：IP黑白名单、函数黑白名单、内网反代、数据缓存、跨语言多数据格式
2. 实际考察发现，只有内网反代功能才是大家需要的，其他功能都极少有人用
3. 缺点：由于当初没有在数据包中加入请求编号或会话编号，多人都挤同房间数据会混乱
4. pip install ksrpc<0.6.0

### 第二代

1. 考虑到大家只关注内网反代，所以决定用更专业的反代工具，如：`frp`等
2. 删减功能，只留`API`调用+`Baisc`认证。
3. 某平台中的`FastAPI`所创建的服务只要访问，`uvicorn`就崩溃，最后决定将客服端和服务端都替换成`aiohttp`
4. `async`和`sync`的互转导致系统非常混乱，清理只留`async`。但所有不改代码的`hack`功能作废
5. pip install ksrpc>=0.6.0

## 工作原理

1. 创建`Web`服务，接收请求后，调用服务器中的`Python`库，将结果二进制封装后返回
2. 客户端将API调用封装，然后向`Web`服务器请求，等待返回
3. 返回结果解包成`Python`对象
4. 反代时`frp`需要公网有服务器进行转发。当然你也可以使用其他组网工具，如`easytier`等

## 安装

```bash
pip install ksrpc -i https://mirrors.aliyun.com/pypi/simple --upgrade
# 或
pip install ksrpc -i https://pypi.org/simple --upgrade
```

## 使用

1. 服务端

```bash
python -m ksrpc.run_app
```

2. 客户端

```python
import asyncio

from ksrpc.client import RpcClient
from ksrpc.connections.http import HttpConnection

URL = 'http://127.0.0.1:8080/api/file'


async def async_main():
    async with HttpConnection(URL, username="admin", password="password123") as conn:
        demo = RpcClient('ksrpc.server.demo', conn)

        print(await demo.test())


asyncio.run(async_main())
```

更多代码参考[examples](https://github.com/wukan1986/ksrpc/tree/main/examples)

内网反代参考[examples_frp](https://github.com/wukan1986/ksrpc/tree/main/examples_frp)

## 参考项目

开发到一定阶段后才发现与`rpyc`这个免注册暴露函数的功能类似，大家也可以去学习一下

https://github.com/tomerfiliba-org/rpyc

## 声明

此库仅供学习交流，请在数据提供方的授权范围内使用。请勿向第三方转发数据