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

!!!一定要自行修改房间号!!!

!pip install ksrpc-0.3.3-py3-none-any.whl --user --upgrade
"""

import asyncio

from loguru import logger

from ksrpc.connections.websocket import WebSocketConnection

# 重试次数，防止忘记关闭Notebook内核导致占用资源
RETRY_COUNT = 30
TOKEN = 'secret-token-2'
# 注意：房间号请设置一个复杂的字符串，一定不要与其他用户的冲突，否则数据会乱
URL = 'ws://127.0.0.1:8000/ws/client?room=HA9527'


async def async_main():
    logger.info('强调!!!使用完后一定要停止内核，防止长期占用资源!!!')

    cnt = RETRY_COUNT
    while cnt > 0:  # 重连次数，约1分钟
        logger.info('try to connect. {}', cnt)
        try:
            # 连接被控端地址（带/client），同时还要指定约定的房间号字符串
            async with WebSocketConnection(URL, token=TOKEN) as conn:
                logger.info('connected')
                recv_count = await conn.reverse(recv_timeout=True, clear_cnt=3)
                # 空闲断开时会走到这一步
                logger.info('recv timeout')
                if recv_count == 0:
                    # 内部空闲超时是60秒，为了快速停止，加快超时设定
                    cnt -= 2
                else:
                    # 底层收到过数据包，外层重新计数
                    cnt = RETRY_COUNT
        except Exception as e:
            logger.info(e)
            # 重试不能太块，一直在重试时，试着点击重启内核
            await asyncio.sleep(5)
            cnt -= 1
    logger.info('done')


if __name__ == '__main__':
    # TODO WebSocket+async要加这两句，否则报错
    import revolving_asyncio

    revolving_asyncio.apply()

    asyncio.run(async_main())
