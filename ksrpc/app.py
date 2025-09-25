import asyncio
import base64
import time
import zlib

import dill as pickle
from aiohttp import web

from ksrpc.caller import switch_call
from ksrpc.config import USER_CREDENTIALS, HOST, PORT, PATH_HTTP, PATH_WS
from ksrpc.utils.chunks import send_in_chunks, data_sender
from ksrpc.utils.key_ import make_key


async def handle(request: web.Request) -> web.StreamResponse:
    buffer = bytearray()
    buf = bytearray()
    async for chunk, end_of_http_chunk in request.content.iter_chunks():
        buf.extend(chunk)
        if end_of_http_chunk:
            if len(buf) == 0:
                continue
            buffer.extend(zlib.decompress(buf))
            buf.clear()

    d = pickle.loads(buffer)
    key = make_key(**d)

    # TOOD 检查key的功能暂时屏蔽
    # if request.match_info.get("key", "") != key:
    #     return web.HTTPForbidden()

    data = await switch_call(**d)
    buffer.clear()

    body = pickle.dumps(data)
    headers = {'Content-Disposition': f"{key}.pkl.chunked.zip"}

    del data
    return web.Response(body=data_sender(body, print), headers=headers)


async def websocket_handler(request: web.Request) -> web.StreamResponse:
    # print(request.url)

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    buffer = bytearray()
    async for msg in ws:
        if msg.type is web.WSMsgType.BINARY:
            buffer.extend(zlib.decompress(msg.data))
        elif msg.type == web.WSMsgType.TEXT:
            if msg.data == "EOF":
                data = await switch_call(**pickle.loads(buffer))
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
    return await handler(request)


def unauthorized_response():
    return web.Response(
        status=401,
        headers={'WWW-Authenticate': 'Basic realm="Restricted Area"'},
        text="Unauthorized"
    )


@web.middleware
async def url_check_middleware(request, handler):
    # URL动态变化，防止重放攻击
    t1 = time.time()
    t2 = float(request.match_info.get("time", "0"))
    if abs(t1 - t2) > 15:
        print("HTTPForbidden:", t1, t2, t1 - t2)
        return web.HTTPForbidden()

    return await handler(request)


def create_app(argv):
    # uv run python -m aiohttp.web -H 0.0.0.0 -P 8080 ksrpc.run_app:sync_app
    app = web.Application(middlewares=[
        url_check_middleware,  # 时间检验
        basic_auth_middleware,  # 注释此行屏蔽Baisc认证
    ])
    app.add_routes([
        # TODO 路径按需修改，更安全
        web.post(PATH_HTTP, handle),
        web.get(PATH_WS, websocket_handler),
    ])
    return app


async def start_server():
    app = create_app([])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)  # 可选：指定端口
    await site.start()
    print(f"Server started at http://{HOST}:{PORT}")
    # 保持服务器运行，直到被中断
    try:
        await asyncio.Future()  # 永久等待
    finally:
        print("Cleanup server")
        await runner.cleanup()
