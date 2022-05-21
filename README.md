# ksrpc
Keep Simple RPC

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

## 服务端安装
1. 安装ksrpc库
> pip install ksrpc[server] -i https://mirrors.aliyun.com/pypi/simple --upgrade
2. 编辑config.py文件，进行ksrpy的功能管理
3. 编辑run_app.py文件，进行FastAPI服务器设置
4. 运行python run_app.py

## 客户端安装
1. 安装ksrpc库
> pip install ksrpc -i https://mirrors.aliyun.com/pypi/simple --upgrade
2. 编辑examples目录下的demo_http.py和demo_websocket.py中对应的服务地址
3. 运行demo_http.py和demo_websocket.py，检查是否运行正常

## 示例
1. 直接可替代的。如`tests`目录下的：os、numpy、pandas、akshare等
    1. 没有在客户端安装相应包的情况下无IDE自动补全功能
2. 需要服务端进行登录等一类处理的。如`server`目录下的，jqdatasdk、tushare、WindPy等
3. 客户端参数无法序列化，需要特殊处理的。如`hack`目录下的jqdatasdk、WindPy等
    1. 需要客户端安装了第三方库，IDE的自动补全功能能用了

```python
from ksrpc import RpcClient
from ksrpc.connections.http import HttpxConnection

conn = HttpxConnection('http://127.0.0.1:8000/api')
conn.timeout = None
math = RpcClient('math', conn, is_async=False)
math.cache_get = True
math.cache_expire = 86400

# 模块中变量获取方法。加了括号
print(math.pi())
print(math.pow(2, 3))
```

```python
# 创建客户连接
from ksrpc import RpcClient
from ksrpc.connections.http import HttpxConnection

conn = HttpxConnection('http://127.0.0.1:8000/api')
conn.timeout = None
client = RpcClient('tushare', conn, is_async=False)
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
1. AkShare(已测)
2. TuShare(已测)
3. rqdatc(已测)
4. jqdatasdk(缺账号，未测)
5. Wind(缺账号，未测)
6. 其它...

## 参考项目
开发到一定阶段后才发现与rpyc这个免注册暴露函数的功能类似，大家也可以去学习一下
https://github.com/tomerfiliba-org/rpyc

