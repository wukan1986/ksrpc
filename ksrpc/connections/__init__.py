import aiohttp


class BaseConnection:
    def __init__(self, url: str, username=None, password=None):
        self._url = url
        if username and password:
            self._auth = aiohttp.BasicAuth(login=username, password=password, encoding="utf-8")
        else:
            self._auth = None

    async def reset(self):
        ...

    async def call(self, module, name, args, kwargs, ref_id):
        ...
