import asyncio


def async_to_sync(func, *args, **kwargs):
    running_loop = asyncio._get_running_loop()
    if running_loop is None:
        if hasattr(asyncio, "run"):
            # 尝试使用 Python 3.7+ 的 asyncio.run()
            return asyncio.run(func(*args, **kwargs))
        else:
            # 回退到手动事件循环管理
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(func(*args, **kwargs))
            finally:
                loop.close()
    else:
        # TODO 已经有loop时没运行，是否有其他解决方法？
        try:
            return running_loop.run_until_complete(func(*args, **kwargs))
        finally:
            pass
