from ksrpc.app.simple_ import main

if __name__ == "__main__":
    # 数据库查询线程中跑时，报StateException('Interruptingcow can only be used from the MainThread.',)
    main(fork=True)
