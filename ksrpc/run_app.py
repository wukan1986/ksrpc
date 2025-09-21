import base64
import pickle
import zlib

from aiohttp import web

from ksrpc.caller import async_call
from ksrpc.config import USER_CREDENTIALS, check_url_path
from ksrpc.utils.chunks import send_in_chunks


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


async def handle(request: web.Request) -> web.StreamResponse:
    check_url_path(request.match_info.get('path', "tmp"))

    buffer = bytearray()
    async for chunk in request.content.iter_chunked(1024 * 64):
        buffer.extend(chunk)

    key, data = await async_call(**pickle.loads(buffer))
    buffer.clear()

    deflate = True
    if deflate:
        body = zlib.compress(pickle.dumps(data))
        headers = {'CONTENT-DISPOSITION': f"{key}.pkl.zip",
                   'Content-Encoding': 'deflate'}
    else:
        body = pickle.dumps(data)
        headers = {'CONTENT-DISPOSITION': f"{key}.pkl"}

    del data
    return web.Response(body=body, headers=headers)


async def websocket_handler(request: web.Request) -> web.StreamResponse:
    check_url_path(request.match_info.get('path', "tmp"))

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    buffer = bytearray()
    async for msg in ws:
        if msg.type is web.WSMsgType.BINARY:
            buffer.extend(zlib.decompress(msg.data))
        elif msg.type == web.WSMsgType.TEXT:
            if msg.data == "EOF":
                key, data = await async_call(**pickle.loads(buffer))
                buffer.clear()
                await send_in_chunks(ws, pickle.dumps(data))
                del data
        elif msg.type == web.WSMsgType.ERROR:
            print('Server WebSocket connection closed with exception %s' % ws.exception())
        elif msg.type is web.WSMsgType.CLOSE:
            print('Server WebSocket connection closed')
            break
    print("End of websocket_handler")
    return ws


def sync_app(argv):
    # uv run python -m aiohttp.web -H 0.0.0.0 -P 8080 ksrpc.run_app:sync_app
    app = web.Application(middlewares=[
        basic_auth_middleware,  # 注释此行屏蔽Baisc认证
    ])
    app.add_routes([
        web.post("/api/{path}", handle),
        web.get("/ws/{path}", websocket_handler),
    ])
    return app


async def async_app():
    # gunicorn ksrpc.run_app:async_app --bind 0.0.0.0:8080 --worker-class aiohttp.GunicornWebWorker
    app = sync_app([])
    return app


if __name__ == '__main__':
    web.run_app(sync_app([]))
