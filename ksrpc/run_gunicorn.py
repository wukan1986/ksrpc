import os

from ksrpc.importer import import_module_from_path

config = os.getenv("CONFIG", "")
if config:
    import_module_from_path("ksrpc.config", config)

from ksrpc.app import create_app

web_app = create_app([])
