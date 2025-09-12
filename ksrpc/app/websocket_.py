"""
WebSocket服务器
1. 提交json格式，返回也json格式。可在浏览器中用JS调用，或通过其它语言访问
2. 提交pickle格式，返回也json格式。内部调用

使用FastAPI搭建的WebSocket服务
1. pip install uvicorn[standard], 必须指定stanadard，否则安装后不支持websocket服务
2. `/ws/json` 可用其它语言调用
3. `/ws/bytes` 内部调用
4. `/ws/client` `/ws/amdin`, 反弹RPC

反向RPC时偶尔出现无响应的情况，应当是大数据量时导致的不稳定，所以自己实现了分片功能
"""
from datetime import datetime
from typing import List, Any, Dict, Union

from fastapi import WebSocket, WebSocketDisconnect, Depends, Query
from fastapi import status
from fastapi.security.utils import get_authorization_scheme_param
from loguru import logger

from .app_ import app
from ..caller import call, before_call
from ..config import IP_BLOCK, IP_ALLOW, ENABLE_RELAY
from ..model import Format, RspModel
from ..serializer.json_ import obj_to_dict, dict_to_json
from ..serializer.pkl_gzip import deserialize, serialize
from ..utils.check_ import check_ip

# 二进制拆包
BYTES_PER_SEND = 1024 * 32


async def get_current_user(ws: WebSocket, token: Union[str, None] = Query(None)):
    from ..config import AUTH_CHECK, AUTH_TOKENS
    if not AUTH_CHECK:
        return 'anonymous'
    authorization: str = ws.headers.get("Authorization")
    scheme, param = get_authorization_scheme_param(authorization)
    # 如果从头取不到token就从query中取
    if param:
        token = param
    return AUTH_TOKENS.get(token, None)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active_connections.remove(ws)

    @staticmethod
    async def send_personal_message(message: str, ws: WebSocket):
        await ws.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


async def _do(ws: WebSocket,
              func: str,

              args: List[Any] = [],
              kwargs: Dict[str, Any] = {},
              fmt: Format = Format.JSON,
              cache_get: bool = True, cache_expire: int = 86400,
              async_remote: bool = True,
              user: str = None,  # 没有用到，用于token认证
              ):
    """实际处理函数"""
    try:
        before_call(ws.client.host, user, func)
        key, buf, data = await call(user, func, args, kwargs, cache_get, cache_expire, async_remote)
    except Exception as e:
        # 主要是处理
        key = type(e).__name__
        # 这里没有缓存，因为这个错误是服务器内部检查
        data = RspModel(status=status.HTTP_401_UNAUTHORIZED,
                        datetime=datetime.now().isoformat(),
                        func=func, args=args, kwargs=kwargs)
        data.type = type(e).__name__
        data.data = repr(e)
        data = data.model_dump() if hasattr(data, 'model_dump') else data.dict()
        buf = serialize(data).read()

    if fmt == Format.PKL_GZIP:
        return buf

    if data is None:
        data = deserialize(buf)

    # DataFrame需要csv格式时走此路径
    if fmt == Format.CSV and data['type'] in ('DataFrame', 'Series'):
        return data['data'].to_csv()

    # JSON格式时，为了方便DataFrame的显示，做一下转换
    data['data'] = obj_to_dict(data['data'])

    return data


@app.websocket("/ws/json")
async def websocket_endpoint_json(websocket: WebSocket, user=Depends(get_current_user)):
    """处理JSON，发送JSON或csv"""
    await manager.connect(websocket)
    try:
        while True:
            req = await websocket.receive_json(mode="text")
            logger.info(req)
            rsp = await _do(websocket, **req, user=user)
            # 部分类型换转json有问题，所以使用特殊的转换函数
            await websocket.send_text(dict_to_json(rsp))
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket("/ws/bytes")
async def websocket_endpoint_bytes(websocket: WebSocket, user=Depends(get_current_user)):
    """处理pkl.gz发送pkl.gz"""
    await manager.connect(websocket)
    try:
        while True:
            req = await websocket.receive_bytes()
            bl = deserialize(req)
            req = b''
            while len(req) < bl:
                req += await websocket.receive_bytes()
            req = deserialize(req)
            logger.info(req)
            req['fmt'] = Format.PKL_GZIP
            b = await _do(websocket, **req, user=user)
            bl = len(b)
            await websocket.send_bytes(serialize(bl).read())
            for i in range(0, len(b), BYTES_PER_SEND):
                await websocket.send_bytes(b[i:i + BYTES_PER_SEND])

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# 房间，分存客户端和管理端，中转时用于查找对应的ws
rooms_client: Dict[str, WebSocket] = {}
rooms_admin: Dict[str, WebSocket] = {}


@app.websocket("/ws/client")
async def websocket_endpoint_client(websocket: WebSocket, room: str, user=Depends(get_current_user)):
    """被控端。肉鸡接入后，等待控制端接入，然后转发到肉鸡，然后转发。必须要进入同一房间"""
    await manager.connect(websocket)
    try:
        if not ENABLE_RELAY:
            raise Exception(f'Relay offline')

        if user is None:
            raise Exception(f"Unauthorized")

        rooms_client[room] = websocket
        while True:
            req = await websocket.receive_bytes()
            # 可以将被控端的二进制解码，然后转成json，实现跨语言，这里先不处理
            await rooms_admin[room].send_bytes(req)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(e)
        manager.disconnect(websocket)
        await websocket.close()


@app.websocket("/ws/admin")
async def websocket_endpoint_admin(websocket: WebSocket, room: str, user=Depends(get_current_user)):
    """控制端。等待控制端接入，然后转发"""
    await manager.connect(websocket)
    try:
        # 确保连上admin的用户有权限
        from ..config import IP_CHECK

        if not ENABLE_RELAY:
            raise Exception(f'Relay offline')

        if IP_CHECK:
            from IPy import IP
            # 两张清单数据提前处理，加快处理速度
            __IP_ALLOW__ = {IP(k): v for k, v in IP_ALLOW.items()}
            __IP_BLOCK__ = {IP(k): v for k, v in IP_BLOCK.items()}
            host = IP(websocket.client.host)
            if not check_ip(__IP_ALLOW__, host, False):
                raise Exception(f'IP Not Allowed, {host} not in allowlist')
            if not check_ip(__IP_BLOCK__, host, True):
                raise Exception(f'IP Not Allowed, {host} in blocklist')

        if user is None:
            raise Exception(f"Unauthorized")

        rooms_admin[room] = websocket
        while True:
            req = await websocket.receive_bytes()
            await rooms_client[room].send_bytes(req)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(e)
        manager.disconnect(websocket)
        await websocket.close()
