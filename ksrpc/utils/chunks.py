# 发送端分块
import sys
import zlib
from io import BytesIO

from ksrpc.utils.tqdm import update_progress


async def data_sender(data, print, chunk_size=1024 * 128):
    file = sys.stderr
    print(f'加载数据: ({len(data):,} bytes) [', end='', file=file)
    data = BytesIO(data)
    chunk = data.read(chunk_size)
    i = -1
    size = 0
    while chunk:
        buf = zlib.compress(chunk)
        size += len(buf)
        yield buf
        i += 1
        update_progress(i, print, file=file)
        chunk = data.read(chunk_size)
    # 会快速的显示到此处，但实际数据还在发送中，建议与客户端接收进度一起看
    print(f'] 压缩完成 ({size:,} bytes) | 底层异步发送中，请勿立即退出！', file=file)


async def send_in_chunks(ws, data, print, chunk_size=1024 * 128):  # 32KB
    # 64KB时，某宽发出的大数据无法zlib解压，所以改成了32KB
    # 将数据分块发送
    file = sys.stderr
    print(f'发送数据: ({len(data):,} bytes) [', end='', file=file)

    j = -1
    size = 0
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        buf = zlib.compress(chunk, 6)
        size += len(buf)
        await ws.send_bytes(buf)
        await ws.send_str("\r\n")
        j += 1
        update_progress(j, print, file=file)
    # 会快速的显示到此处，但实际数据还在发送中，建议与客户端接收进度一起看
    print(f'] 压缩完成 ({size:,} bytes) | 底层异步发送中，请勿立即退出！', file=file)

    # 发送结束标志
    await ws.send_str("EOF")
