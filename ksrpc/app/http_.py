"""
HTTP服务端
1. 提交json，返回csv或json。通过浏览器访问，或通过其它语言，可以走此通道
2. 提交pickle，返回pickle。python语言限定，这种方法更强大

通过FastAPI搭建的服务
1. 大量使用异步， 所以需要被调用的API也能转成异步，否则会阻塞之后的请求
2. 其它语言用户请走`/api/get`或`/api/post`
3. `/api/file`为python内部使用

"""
from typing import Dict, Any, List

from fastapi import Query, Body, File, Depends
from fastapi.requests import Request
from fastapi.responses import PlainTextResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer

from .app_ import app
from ..caller import call
from ..config import AUTH_TOKENS, AUTH_CHECK
from ..model import RspFmt
from ..serializer.json_ import obj_to_dict
from ..serializer.pkl_gzip import deserialize

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not AUTH_CHECK:
        return 'anonymous'
    return AUTH_TOKENS.get(token, None)


@app.get("/api/get")
async def api_get(request: Request,
                  func: str = Query(..., min_length=1),

                  rsp_fmt: RspFmt = Query(RspFmt.CSV),
                  cache_get: bool = Query(True), cache_expire: int = Query(86400, lt=86400 * 15),
                  user: str = Depends(get_current_user),
                  ):
    """无参数函数。可以通过get发起请求。可在浏览器中直接发起"""
    return await _do(**locals())


@app.post("/api/post")
async def api_post(request: Request,
                   args: List[Any] = Body([]),
                   kwargs: Dict[str, Any] = Body({}),

                   func: str = Query(..., min_length=1),

                   rsp_fmt: RspFmt = Query(RspFmt.CSV),
                   cache_get: bool = Query(True), cache_expire: int = Query(86400, lt=86400 * 15),
                   user: str = Depends(get_current_user),
                   ):
    """简单参数函数。可通过post请求，使用body区传json参数。可跨语言。可用Postman发起"""
    return await _do(**locals())


@app.post("/api/file")
async def api_file(request: Request,
                   file: bytes = File(...),  # file要写在最前面，否则报错

                   func: str = Query(..., min_length=1),

                   rsp_fmt: RspFmt = Query(RspFmt.CSV),
                   cache_get: bool = Query(True), cache_expire: int = Query(86400, lt=86400 * 15),
                   user: str = Depends(get_current_user),
                   ):
    """复杂参数函数。通过文件上传二进制方式。不可跨语言。"""
    return await _do(**locals(), **deserialize(file))


async def _do(request: Request,
              func: str,

              args: List[Any] = [],
              kwargs: Dict[str, Any] = {},

              rsp_fmt: RspFmt = RspFmt.CSV,
              cache_get: bool = True, cache_expire: int = 86400,
              file: bytes = None,  # 用于兼容文件上传模式，但实际没有使用
              user: str = None,  # 没有用到，用于token认证
              ):
    """实际处理函数"""

    # 分解调用方法
    key, buf, data = await call(request.client.host, user, func, args, kwargs, cache_get, cache_expire)

    # 直接二进制返回
    if rsp_fmt == RspFmt.PKL_GZIP:
        r = StreamingResponse(iter([buf]), media_type="application/octet-stream")
        content_disposition = f'attachment; filename="{key}.{RspFmt.PKL_GZIP}"'
        r.headers.setdefault("content-disposition", content_disposition)
        return r

    # 从缓存中获取的，但又要转成json等其它功能，需要解码
    if data is None:
        data = deserialize(buf)

    # DataFrame需要csv格式时走此路径
    if rsp_fmt == RspFmt.CSV and data.type in ('DataFrame', 'Series'):
        return PlainTextResponse(data['data'].to_csv())

    # JSON格式时，为了方便DataFrame的显示，做一下转换
    data['data'] = obj_to_dict(data['data'])

    return data