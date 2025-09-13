# ksrpc

Keep Simple RPC。免注册远程过程调用

## 项目背景

团队里常常需要通过平台下载各数据，但只有一套账号。通常的方案如下：

1. 一个账号大家共用。最简单粗暴
    1. 账号还能登录平台的其它功能，不便于分享
    2. 账号可能有在线数上限，会导致互踢
    3. 不同成员可能重复下载相同数据，同一成员也可能反复下载相同数据
2. 由IT团队将数据提前下载过来。人力成本最高
    1. IT团队需要提前规划部署，并向研究团队推广
    2. 不同数据需要IT团队针对性的提前准备下载，时效性一般
    3. 有些数据只是临时少量需要，需求变化快

如果搭建一套服务，客户端不需账号，基本不用改动代码，是否解决多成员分享问题？所以这个项目就是为了API转发，只是后来发现本质上是RPC

## 目标及特性

1. 不修改第三方API源代码，实现客户端免登录
2. 新接口与原接口一致，基本不用改动代码
3. 数据缓存功能，减少下载次数。针对有数据有限额、调用次数有限制等情况
4. 跨语言，能将大量Python的数据API转成HTTP服务，由其它语言调用
5. 既支持同步调用，又支持异步调用

## 应用场景

1. 数据缓存转发
2. 源代码保护。核心代码不提供，只向外暴露服务
3. 远程控制。可调os、sys等库

## 与其它RPC的区别

1. 免注册就可以向外自动暴露所有API
    1. 不得不添加函数白名单与黑名单功能
    2. 添加了简易版的token认证功能
2. 所有API都自动暴露，但并不是所有API都能正常使用。例如：
    1. 输入与输出无法序列化和反序列化
    2. 部分API使用方法特殊，也可能无法使用
    3. 数据量太大，序列化、网络传输都不太现实
3. 可先选择不同的通讯方式，目前提供的方式有：HTTP、WebSocket
4. 出于数据版权保护，默认添加了IP地址校验开关，限制只在内网使用
5. 多人使用时，少数人超量使用，所以又添加了数据量限额功能

## 服务端安装

1. 安装`ksrpc`库

> pip install ksrpc[server] -i https://mirrors.aliyun.com/pypi/simple --upgrade

2. 直接运行`python -m ksrpc.run_app`, 观察提示的`config.py`文件路径
3. 编辑`config.py`文件，进行`ksrpy`的功能管理。如权限配置等`ENABLE_SERVER = True`
4. 再次运行`python -m ksrpc.run_app`
5. 确保服务器上防火墙已经开放对应端口

## 客户端安装

1. 安装`ksrpc`库

> pip install ksrpc[client] -i https://mirrors.aliyun.com/pypi/simple --upgrade

2. 编辑`examples`目录下的`demo_http.py`和`demo_websocket.py`中对应的服务地址
3. 运行`demo_http.py`和`demo_websocket.py`，检查是否运行正常

## 示例

1. 直接可替代的。如`tests`目录下的：os、numpy、pandas、akshare等
    1. 客户端没有安装相应包的情况下，IDE无法自动补全
2. 需要服务端进行登录等一类处理的。如`server`目录下的，jqdatasdk、tushare、WindPy等
3. 客户端参数无法序列化，需要特殊处理的。如`hack`目录下的jqdatasdk、WindPy等
    1. 需要客户端安装第三方库，IDE的自动补全功能正常

```python
from ksrpc.rpc_client import RpcClient
from ksrpc.connections.http import HttpxConnection

conn = HttpxConnection('http://127.0.0.1:8000/api/file')
math = RpcClient('math', conn, async_local=False)
math.cache_get = True
math.cache_expire = 86400

# 模块中变量获取方法。加了括号
print(math.pi())
print(math.pow(2, 3))
```

```python
# 创建客户连接
from ksrpc.rpc_client import RpcClient
from ksrpc.connections.http import HttpxConnection

conn = HttpxConnection('http://127.0.0.1:8000/api/file')
client = RpcClient('tushare', conn, async_local=False)
client.cache_get = True
client.cache_expire = 86400

# 对原版库进行定制处理，需要已经安装了原版库
from ksrpc.hack.tushare import hack

hack(client)

# 原版代码可都保持不变
import tushare as ts

ts.set_token('TUSHARE_TOKEN')
pro = ts.pro_api()
df = pro.trade_cal(exchange='', start_date='20210901', end_date='20211231')
print(df)
df = pro.daily(ts_code='000001.SZ,600000.SH', start_date='20180701', end_date='20180718')
print(df)
```

## 部分支持转发的库

1. [AkShare](tests/akshare_.py)(已测)
2. TuShare [方法一](examples/tushare_hack.py) [方法二](examples/tushare_client.py)(已测)
3. [rqdatac](examples/rqdatac_hack.py)(已测)
4. [jqdatasdk](examples/jqdatasdk_hack.py)(缺账号，未测)
5. [Wind](examples/wind_hack.py)(缺账号，未测)
6. 其它...

## 跨语言开发文档

跨语言示例代码在`lang`目录下
[跨语言开发文档](lang/)

## 声明

此库仅供学习交流，请在数据提供方的授权范围内使用。请勿向第三方转发数据

## 反代RPC - 第一代

如果提供服务的机器在内网，无法搭建服务，也无法直接访问怎么办？参考Reverse Shell的概念，本项目提供了Reverse RPC功能。它在3台电脑中安装了
`ksrpc`

1. 公网服务器上安装`pip install ksrpc[server]`，修改配置，运行`python -m ksrpc.run_app`，记下公网IP
2. 内网服务器上安装`pip install ksrpc[client]`(如果网络受限，可下载whl文件本地安装)，修改`rpc_reverse.py`中为公网IP，运行
   `python rpc_reverse.py`。此代码可粘贴到Notebook中运行
3. 个人电脑上安装`pip install ksrpc[client]`，编辑`examples/demo_reverse.py`中为公网IP，运行，观察结果
4. 注意地址不同，内网被控端连接公网IP下的`/client`, 个人电脑连接公网IP下的`/admin`，并且要用完全一样的房间号
5. 默认情况下，`config.py`中的`ENABLE_RELAY = True`已经开启

## 反代RPC - 第二代

第一代有局限性，必须要在同一房间号，一次只能一个请求，如果同时发起多个请求，会出现数据混乱的情况。

第二代采用更简化的方法。只搭建HTTP服务，反代工作交给第三方，如`frp`。这样免去反代代码，库更简洁。也可以定制更多功能

细节请看`examples_frp\README.md`

## 参考项目

开发到一定阶段后才发现与`rpyc`这个免注册暴露函数的功能类似，大家也可以去学习一下
https://github.com/tomerfiliba-org/rpyc

