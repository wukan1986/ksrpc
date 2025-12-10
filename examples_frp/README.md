# frp

- 下载地址：https://github.com/fatedier/frp/releases  某宽平台需下载`*_linux_amd64.tar.gz`
- 文档地址：https://gofrp.org/zh-cn/

## 配置

1. 下载合适的`frp`压缩包
2. 根据自己的实际情况配置`frpc.toml`中的`serverAddr`为公网服务器(A)`IP`即可，其他参数可按需修改
3. 公网服务器(A)上传`frps.toml`和`frps`。防火墙开放端口`bindPort = 7000`、`remotePort = 7001`和`vhostHTTPPort = 7002`
    - 先运行`chmod 777 frps`
    - 再运行`./frps -c ./frps.toml`
    - ~~试验成功后可改为`nohup ./frps -c ./frps.toml > frps.log 2>&1 &`~~
4. 内网服务器(B)上传`frpc.toml`和`frpc`,以及`ksrpc.ipynb`和`frpc.ipynb`
5. 内网服务器(B)`Jupyter Notebook`中打开`ksrpc.ipynb`
    - 先运行`!pip install ksrpc --user --upgrade`
    - 再运行`!python -m ksrpc.run_app`
6. 内网服务器(B)`Jupyter Notebook`中打开`frpc.ipynb`
    - 先运行`!chmod 777 frpc`
    - 再运行`!./frpc -c ./frpc.toml`
7. 个人电脑(C)安装`pip install ksrpc`
    - 编辑`demo_http.py`中地址为`serverAddr`的IP,端口为`remotePort = 7001`
8. `ksrpc.ipynb`和`frpc.ipynb`用完后一定要`重启内核`，以免长时间占用资源

## 推荐

推荐以后只运行`ksrpc_frpc.ipynb`，它启动了两个子进程并维护。含自动重启和闲时关闭功能

## 安全

1. `auth.token`用于保证`frps`提供的反代服务只有认证过的`frpc`才能打洞
2. `httpUser`和`httpPassword`提供`Basic`认证功能，防止外人访问服务
3. `ksrpc`也提供了`Basic`认证，支持多用户。（推荐）

## bindPort = 80 如何设置

1. `sudo ss -tanlp` # 查看是哪个应用占用了80端口，参考应用的文档进行调整
2. 编辑`frps.toml`中的`bindPort = 80`，编辑`frpc.toml`中的`serverPort = 80`
3. `sudo ./frps -c ./frps.toml` # 进行测试
4. `sudo nohup ./frps -c ./frps.toml &` # 长期运行

## 内存崩溃问题

1. 在使用过程中会出现内存占用过多而崩溃的情况。如何正确释放内存还需调试
2. `ksrpc_frpc.ipynb`中的脚本会在子进程崩溃时重新启动

# 没有公网服务器怎么办？

1. 使用公开免费的服务器，如：`freefrp`、`afrp`。但网络稳定性差，一定要在开发代码时加上断线重试和数据缓存
2. 使用`STUN内网穿透`技术，将`frps`的`7000`端口暴露到公网，注意：公网地址和端口是随机的，不适用限制了端口的平台

## STUN内网穿透

1. `lucky`可以部署在路由器、NAS、PC。https://release.66666.host/ 下载合适版本
2. 直接本地运行`frps -c frps.toml`启动服务
3. 启动`lucky`，进入到`STUN内网穿透`,添加规则
4. 穿透类型`IPv4-TCP`，`NAT-PMP`开启，`NAT-PMP`网关地址为路由器地址，目标地址`127.0.0.0`，目标端口`7000`
5. 记下穿透后地址，例如：`123.123.123.123:45678`。IP可以用DDNS，但端口号会动态变化
6. 然后回到 内网服务器(B)，修改`frpc.toml`中的`serverAddr = "123.123.123.123"`和`serverPort = 45678`
7. 启动`ksrpc_frpc.ipynb`，查看连接是否成功
8. 修改 个人电脑(C) 编辑`demo_http.py`中地址为`127.0.0.1`,端口为`remotePort = 7001`