import os

from ksrpc.importer import import_module_from_path


def main():
    from ksrpc.app import start_server
    from ksrpc.utils.async_ import async_to_sync

    try:
        async_to_sync(start_server)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    # 加载配置文件
    config = os.getenv("CONFIG_SERVER", "")
    if config:
        import_module_from_path("ksrpc.config_server", config)

    main()
