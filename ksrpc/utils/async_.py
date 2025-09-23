import asyncio


def async_wrapper(func, *args, **kwargs):
    try:
        # 尝试使用 Python 3.7+ 的 asyncio.run()
        return asyncio.run(func(*args, **kwargs))
    except AttributeError:
        # 回退到手动事件循环管理
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(func(*args, **kwargs))
        finally:
            loop.close()
