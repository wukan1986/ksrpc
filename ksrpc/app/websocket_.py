"""
WebSocket服务器
1. 提交json格式，返回也json格式。可在浏览器中用JS调用，或通过其它语言访问
2. 提交pickle格式，返回也json格式。内部调用

使用FastAPI搭建的WebSocket服务
1. pip install uvicorn[standard], 必须指定stanadard，否则安装后不支持websocket服务
2. `/ws/json` 可用其它语言调用
3. `/ws/bytes` 内部调用

"""
from typing import List, Any, Dict, Union

from fastapi import WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.security.utils import get_authorization_scheme_param
from loguru import logger

from .app_ import app
from ..caller import call
from ..config import AUTH_CHECK, AUTH_TOKENS
from ..model import Format
from ..serializer.json_ import obj_to_dict, dict_to_json
from ..serializer.pkl_gzip import deserialize


async def get_current_user(ws: WebSocket, token: Union[str, None] = Query(None)):
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
              user: str = None,  # 没有用到，用于token认证
              ):
    """"""
    # 分解调用方法
    key, buf, data = await call(ws.client.host, user, func, args, kwargs, cache_get, cache_expire)

    if fmt == Format.PKL_GZIP:
        return buf

    if data is None:
        data = deserialize(buf)

    # JSON格式时，为了方便DataFrame的显示，做一下转换
    data['data'] = obj_to_dict(data['data'])

    return data


@app.websocket("/ws/json")
async def websocket_endpoint_json(websocket: WebSocket, user=Depends(get_current_user)):
    await manager.connect(websocket)

    try:
        while True:
            req = await websocket.receive_json(mode="text")
            logger.info(req)
            rsp = await _do(websocket, **req, user=user, fmt=Format.JSON)
            # 部分类型换转json有问题，所以使用特殊的转换函数
            await websocket.send_text(dict_to_json(rsp))

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket("/ws/bytes")
async def websocket_endpoint_bytes(websocket: WebSocket,
                                   user=Depends(get_current_user)):
    await manager.connect(websocket)

    try:
        while True:
            req = await websocket.receive_bytes()
            req = deserialize(req)
            logger.info(req)
            rsp = await _do(websocket, **req, user=user, fmt=Format.PKL_GZIP)
            # 部分类型换转json有问题，所以使用特殊的转换函数
            await websocket.send_bytes(rsp)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
