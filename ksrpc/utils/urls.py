import time

from aiohttp import web


class BaseURL:
    """
    为防路径扫描，使用动态路径
    """

    def __init__(self, url: str = 'http://127.0.0.1:8080/api/file'):
        self._url = url

    def __call__(self, *args, **kwargs):
        """由客户端使用"""
        return self._url

    def check(self, request: web.Request):
        """由服务端使用"""
        path = request.match_info.get('path', '')
        assert path == 'file'


class TimeURL(BaseURL):
    """时间动态路径"""

    def __init__(self, url: str = 'ws://127.0.0.1:8080/ws/{}'):
        super().__init__(url)

    def __call__(self, *args, **kwargs):
        """由客户端使用"""
        url = self._url.format(int(time.time()))
        print('Use URL:', url)
        return url

    def check(self, request: web.Request):
        """由服务端使用"""
        path = request.match_info.get('path', '0')
        assert abs(time.time() - int(path)) < 30
