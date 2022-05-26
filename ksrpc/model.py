from enum import Enum
from typing import List, Any, Dict

# from fastapi import status
from pydantic import BaseModel


class Format(str, Enum):
    JSON = 'json'  # 请求和响应用Json可以跨语言
    PKL_GZIP = 'pkl.gz'  # pickle格式再压缩，可用于网络传输和缓存，限定客户端为python语言
    CSV = 'csv'  # 响应是DataFrame时，返回CSV格式。其它语言解析时可能比较容易


class RspModel(BaseModel):
    # 状态
    status: int = 200  # status.HTTP_200_OK
    # 发生时间
    datetime: str = 'now'
    # #请求信息
    func: str = 'call'
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}

    # #响应信息
    type: str = ''
    data: Any = None


class ReqModel(BaseModel):
    # #以下在query区，进行提交
    func: str = 'call'
    fmt: Format = Format.CSV
    cache_get: bool = True
    cache_expire: int = 86400

    # #以下在body区使用json格式或二进制格式提交
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}
