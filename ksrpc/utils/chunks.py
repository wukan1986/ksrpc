# 发送端分块
import sys
import zlib


async def send_in_chunks(ws, data, chunk_size=1024 * 32):  # 32KB
    # 64KB时，某宽发送的大数据无法zlib解压
    # 将数据分块发送
    print(f'发送数据: {len(data)} ', end='', file=sys.stderr)

    for i in range(0, len(data), chunk_size):
        print('>', end='', file=sys.stderr)
        chunk = data[i:i + chunk_size]
        await ws.send_bytes(zlib.compress(chunk, 6))
        print('\b=', end='', file=sys.stderr)
    print(' 发送完成', file=sys.stderr)

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
