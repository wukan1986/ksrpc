import base64

from aiohttp import web
from multidict import MultiDict

from ksrpc.caller import async_call
from ksrpc.config import USER_CREDENTIALS, check_url_path
from ksrpc.serializer.pkl_gzip import deserialize


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

    form = await request.post()  # 小心提交大文件导致内存溢出
    file = form['file'].file.read()
    del form

    key, buf, data = await async_call(**deserialize(file))
    del file
    del data
    rsp = web.Response(body=buf, headers=MultiDict({'CONTENT-DISPOSITION': f"{key}.pkl.gz"}))
    del buf
    del key
    return rsp


async def websocket_handler(request: web.Request) -> web.StreamResponse:
    check_url_path(request.match_info.get('path', "tmp"))

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type is web.WSMsgType.BINARY:
            key, buf, data = await async_call(**deserialize(msg.data))
            del key
            del data
            await ws.send_bytes(buf)
            del buf
        elif msg.type == web.WSMsgType.ERROR:
            print('ws connection closed with exception %s' % ws.exception())
        elif msg.type is web.WSMsgType.CLOSE:
            break

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
