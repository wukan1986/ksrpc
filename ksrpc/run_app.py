# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author     :wukan
# @License    :(C) Copyright 2022, wukan
# @Date       :2022-05-22
"""
HTTP/WebSocket服务端入口
"""
import uvicorn

# HTTP服务
from ksrpc.app.http_ import *  # noqa
# WebSocket服务
from ksrpc.app.websocket_ import *  # noqa
from ksrpc.config import HOST, PORT


def main():
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
