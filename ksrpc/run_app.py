def main():
    from ksrpc.app import start_server
    from ksrpc.utils.async_ import async_to_sync

    try:
        async_to_sync(start_server)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
