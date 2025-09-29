# 注意：属性名和模块名相同时,只能取到属性名，想取到模块
# RpcClient("ksrpc.server.demo")一定要写全
#
# server = RpcClient("ksrpc.server")
# server.demo # 重名取到的是属性，没有重名，取到的是模块
demo = "654321"
