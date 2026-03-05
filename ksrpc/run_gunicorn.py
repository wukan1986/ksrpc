import os

from ksrpc.importer import import_module_from_path

# 加载配置文件
config = os.getenv("CONFIG_SERVER", "")
if config:
    import_module_from_path("ksrpc.config_server", config)

from ksrpc.app import create_app

web_app = create_app([])
