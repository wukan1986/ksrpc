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
9. 配置好，推荐以后只运行`ksrpc_frpc.ipynb`，它启动了两个子进程并维护

## 安全

1. `auth.token`用于保证`frps`提供的反代服务只有认证过的`frpc`才能打洞
2. `httpUser`和`httpPassword`提供`Basic`认证功能，防止外人访问服务
3. `ksrpc`也提供了`Basic`认证，支持多用户。（推荐）

## bindPort = 80 如何设置

1. `sudo ss -tanlp` # 查看是哪个应用占用了80端口，参考应用的文档进行调整
2. 编辑`frps.toml`中的`bindPort = 80`，编辑`frpc.toml`中的`serverPort = 80`
3. `sudo ./frps -c ./frps.toml` # 进行测试
4. `sudo nohup ./frps -c ./frps.toml > frps.log 2>&1 &` # 长期运行

## 内存崩溃问题

1. 在使用过程中会出现内存占用过多而崩溃的情况。如何正确释放内存还需调试
2. `ksrpc_frpc.ipynb`中的脚本会在子进程崩溃时重新启动

