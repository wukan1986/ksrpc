import asyncio
import base64
import os
import time
import zlib
from urllib.parse import unquote

import dill as pickle
from aiohttp import web

from ksrpc.importer import import_module_from_path

# 加载配置文件
config = os.getenv("CONFIG_SERVER", "")
if config:
    import_module_from_path("ksrpc.config_server", config)

from ksrpc.caller import switch_call, async_call  # noqa
from ksrpc.config_server import USER_CREDENTIALS, HOST, PORT, PATH, TIMESTAMP_CHECK, USER_RULES
from ksrpc.utils.chunks import send_in_chunks, data_sender, CHUNK_BORDER, CHUNK_BORDER_BYTES  # noqa


async def handle_generate_204(request: web.Request) -> web.StreamResponse:
    """网络测试"""
    return web.HTTPNoContent()


# async def handle_http(request: web.Request) -> web.StreamResponse:
#     """post请求，一次性请求，无法传大数据，302重定向丢失数据区"""
#     buff = await request.read()
#     data = await async_call(**pickle.loads(zlib.decompress(buff)))
#
#     body = pickle.dumps(data)
#     headers = {'Content-Disposition': f"{id(request)}.pkl.chunked.zip"}
#
#     del data
#     return web.Response(body=data_sender(body, print), headers=headers)


async def handle_chunk(request: web.Request) -> web.StreamResponse:
    """307重定向后，chunk传输数据为空，不得不放弃"""
    buffer = bytearray()
    buf = bytearray()
    async for chunk, end_of_chunk in request.content.iter_chunks():
        buf.extend(chunk)

        bs = buf.split(CHUNK_BORDER_BYTES)
        # 没有出现分隔符，直接返回
        if len(bs) == 1:
            continue

        # 出现了分隔符
        for j, b in enumerate(bs):
            if j == len(bs) - 1:
                buf.clear()
                buf.extend(b)
                continue

            buffer.extend(zlib.decompress(b))

    rules = request['rules']
    data = await async_call(rules, **pickle.loads(buffer))
    buffer.clear()

    body = pickle.dumps(data)
    headers = {'Content-Disposition': f"{id(request)}.pkl.chunked.zip"}

    del data
    return web.Response(body=data_sender(body, print), headers=headers)


async def websocket_handler(request: web.Request) -> web.StreamResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    buffer = bytearray()
    buf = bytearray()
    async for msg in ws:
        if msg.type is web.WSMsgType.BINARY:
            buf.extend(msg.data)
        elif msg.type == web.WSMsgType.TEXT:
            if msg.data == CHUNK_BORDER:
                buffer.extend(zlib.decompress(buf))
                buf.clear()
            elif msg.data == "EOF":
                rules = request['rules']
                data = await async_call(rules, **pickle.loads(buffer))
                buffer.clear()
                await send_in_chunks(ws, pickle.dumps(data), print)
                del data
        elif msg.type == web.WSMsgType.ERROR:
            print('Server WebSocket connection closed with exception %s' % ws.exception())
        elif msg.type is web.WSMsgType.CLOSE:
            print('Server WebSocket connection closed')
            break
    print("End of websocket_handler")
    return ws


@web.middleware
async def basic_auth_middleware(request, handler):
    # 检查是否需要跳过认证的路由
    if request.path == '/public':
        return await handler(request)

    # 获取 Authorization 头
    auth_header = request.headers.get('Authorization')

    if auth_header is None or not auth_header.startswith('Basic '):
        return unauthorized_response()

    # 解码凭证
    try:
        auth_bytes = base64.b64decode(auth_header[6:])
        auth_str = auth_bytes.decode('utf-8')
        username, password = auth_str.split(':', 1)
    except (ValueError, UnicodeDecodeError):
        return unauthorized_response()

    # 验证凭证
    if USER_CREDENTIALS.get(username) != password:
        return unauthorized_response()

    # 认证通过，添加用户名到请求对象
    request['user'] = username
    request['rules'] = USER_RULES.get(username)
    return await handler(request)


def unauthorized_response():
    return web.Response(
        status=401,
        headers={'WWW-Authenticate': 'Basic realm="Restricted Area"'},
        text="Unauthorized"
    )


@web.middleware
async def timestamp_middleware(request, handler):
    # 不检查
    if TIMESTAMP_CHECK <= 0:
        return await handler(request)

    # URL动态变化，防止重放攻击
    t1 = float(request.headers.get('X-Timestamp', "0"))
    t2 = time.time()
    if abs(t1 - t2) > TIMESTAMP_CHECK:
        return web.HTTPForbidden(text=f"The time difference between server and client is too large, {t1} - {t2} = |{t1 - t2:.1f}| > {TIMESTAMP_CHECK}")

    return await handler(request)


def create_app(argv):
    # uv run python -m aiohttp.web -H 0.0.0.0 -P 8080 ksrpc.run_app:sync_app
    app = web.Application(
        middlewares=[
            timestamp_middleware,  # 时间检验
            basic_auth_middleware,  # 注释此行屏蔽Baisc认证
        ])

    path = unquote(PATH.rstrip('/'))
    print("PATH:", path)
    app.add_routes([
        # web.post(f"{path}/http", handle_http),
        # web.get(f"{path}/http", handle_http), # 302后丢弃数据区
        web.post(f"{path}/generate_204", handle_generate_204),
        web.get(f"{path}/generate_204", handle_generate_204),
        web.post(f"{path}/chunk", handle_chunk),
        web.get(f"{path}/ws", websocket_handler),
    ])
    return app


async def start_server():
    app = create_app([])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=HOST, port=PORT)  # 可选：指定端口
    await site.start()
    print(f"Server started at http://{HOST}:{PORT}")
    # 保持服务器运行，直到被中断
    try:
        await asyncio.Future()  # 永久等待
    finally:
        print("Cleanup server")
        await runner.cleanup()
