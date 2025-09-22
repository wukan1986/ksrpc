from aiohttp import web

from ksrpc import config
from ksrpc.app import sync_app

if __name__ == '__main__':
    print(f"Current config:", config.__file__)
    web.run_app(sync_app([]))
