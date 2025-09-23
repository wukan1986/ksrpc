import asyncio
import base64
import pickle
import zlib

from aiohttp import web

from ksrpc.caller import switch_call
from ksrpc.config import USER_CREDENTIALS, URL_CHECKER, HOST, PORT
from ksrpc.utils.chunks import send_in_chunks, data_sender


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
    try:
        URL_CHECKER.check(request)
    except (AssertionError, ValueError):
        return web.HTTPForbidden()

    return await handler(request)


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

    key, data = await switch_call(**pickle.loads(buffer))
    buffer.clear()

    body = pickle.dumps(data)
    headers = {'Content-Disposition': f"{key}.pkl.chunked.zip"}

    del data
    return web.Response(body=data_sender(body, print), headers=headers)


async def websocket_handler(request: web.Request) -> web.StreamResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    buffer = bytearray()
    async for msg in ws:
        if msg.type is web.WSMsgType.BINARY:
            buffer.extend(zlib.decompress(msg.data))
        elif msg.type == web.WSMsgType.TEXT:
            if msg.data == "EOF":
                key, data = await switch_call(**pickle.loads(buffer))
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


def create_app(argv):
    # uv run python -m aiohttp.web -H 0.0.0.0 -P 8080 ksrpc.run_app:sync_app
    app = web.Application(middlewares=[
        basic_auth_middleware,  # 注释此行屏蔽Baisc认证
        url_check_middleware,
    ])
    app.add_routes([
        web.post("/api/{path}", handle),
        web.get("/ws/{path}", websocket_handler),
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
    await asyncio.Future()  # 永久等待
