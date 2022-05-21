from enum import Enum
from typing import List, Any, Dict, Union

from fastapi import status
from pydantic import BaseModel


class ReqFmt(str, Enum):
    JSON = 'json'  # 请求和响应用Json可以跨语言
    PKL_GZIP = 'pkl.gz'  # pickle格式再压缩，可用于网络传输和缓存，限定客户端为python语言


class RspFmt(str, Enum):
    JSON = 'json'  # 请求和响应用Json可以跨语言
    PKL_GZIP = 'pkl.gz'  # pickle格式再压缩，可用于网络传输和缓存，限定客户端为python语言
    CSV = 'csv'  # 响应是DataFrame时，返回CSV格式。其它语言解析时可能比较容易


class RspModel(BaseModel):
    status: int = status.HTTP_200_OK
    datetime: str = 'now'
    func: str = 'call'
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}
    type: str = ''
    data: Any = None


class ReqModel(BaseModel):
    func: str = 'call'
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}
    req_fmt: ReqFmt = RspFmt.JSON
    rsp_fmt: RspFmt = RspFmt.CSV
    cache_get: bool = True
    cache_expire: int = 86400


class User(BaseModel):
    username: str
    disabled: Union[bool, None] = None


class UserInDB(User):
    hashed_password: str
