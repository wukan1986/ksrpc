class BaseConnection:
    def __init__(self, url):
        self._url = url

    def get_url(self):
        if isinstance(self._url, str):
            return self._url
        else:
            # 可以定制URL，比如随机生成与本地时间有关的url
            return self._url()

    async def reset(self):
        ...

    async def call(self, module, name, args, kwargs):
        ...
