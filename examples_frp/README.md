# frp

- 下载地址：https://github.com/fatedier/frp/releases  某宽平台需下载`*_linux_amd64.tar.gz`
- 文档地址：https://gofrp.org/zh-cn/

## 配置

1. 下载合适的`frp`压缩包
2. 根据自己的实际情况配置`frpc.toml`中的`serverAddr`为公网服务器(A)`IP`即可，其他参数可按需修改
3. 公网服务器(A)上传`frps.toml`和`frps`。防火墙开放端口`bindPort = 7000`和`remotePort = 7001`
    - 先运行`chmod 777 frps`
    - 再运行`./frps -c ./frps.toml`
4. 内网服务器(B)上传`frpc.toml`和`frpc`,以及`ksrpc.ipynb`和`frpc.ipynb`
5. 内网服务器(B)`Jupyter Notebook`中打开`ksrpc.ipynb`
    - 先运行`!pip install ksrpc --user --upgrade`
    - 再运行后面的单元格
6. 内网服务器(B)`Jupyter Notebook`中打开`frpc.ipynb`
    - 先运行`!chmod 777 frpc`
    - 再运行`!./frpc -c ./frpc.toml`
7. 个人电脑(C)安装`pip install ksrpc[client]`
    - 编辑`demo_http.py`中地址为`serverAddr`的IP,端口为`remotePort = 7001`
8. `ksrpc.ipynb`和`frpc.ipynb`用完后一定要`重启内核`，以免长时间占用资源