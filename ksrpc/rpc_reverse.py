# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author     :wukan
# @License    :(C) Copyright 2022, wukan
# @Date       :2022-05-26
"""
reverse rpc，反弹rpc
如果要调用的服务器在内网，并且由于条件所限，无法安装更多的库
所以这里只需小规模的安装即可

以下代码可以直接复制在Notebook中使用
"""

import asyncio

from loguru import logger

from ksrpc.connections.websocket import WebSocketConnection

TOKEN = 'secret-token-2'
URL = 'ws://127.0.0.1:8000/ws/client?room=9527'


async def async_main():
    while True:
        logger.info('try to connect')
        try:
            # 连接被控端地址（带/client），同时还要指定约定的房间号
            async with WebSocketConnection(URL, token=TOKEN) as conn:
                logger.info('connected')
                await conn.reverse()
        except Exception as e:
            logger.info(e)
            # 重试不能太块，一直在重试时，试着点重启内核
            await asyncio.sleep(5)


if __name__ == '__main__':
    asyncio.run(async_main())
