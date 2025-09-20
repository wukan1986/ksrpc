# 发送端分块
import zlib

from tqdm import tqdm


async def send_in_chunks(ws, data, chunk_size=65536):  # 64KB
    # 将数据分块发送
    iterable = range(0, len(data), chunk_size)
    if len(data) > chunk_size * 4:
        # 超过一定大小才显示进度条
        iterable = tqdm(iterable)

    for i in iterable:
        chunk = data[i:i + chunk_size]
        await ws.send_bytes(zlib.compress(chunk, 6))

    # 发送结束标志
    await ws.send_str("EOF")


"""
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    buffer = bytearray()

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.BINARY:
            buffer.extend(msg.data)
        elif msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == "EOF":
                # 处理完整数据
                await handle_complete_data(bytes(buffer))
                buffer.clear()
            else:
                # 处理文本消息
                pass
        elif msg.type == aiohttp.WSMsgType.ERROR:
            break

    return ws
"""
