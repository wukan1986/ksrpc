# 应当用计划任务，每天凌晨0点执行
# 每天按需求重值部分用户的配额信息，第二天即可使用
import asyncio

from ksrpc.cache import async_cache_setex, async_cache_get, async_cache_keys


async def test():
    user = 'nobody'
    module = 'demo'
    func_name = 'demo.test'

    m_quota_key = f'QUOTA/{user}/{module}'
    f_quota_key = f'QUOTA/{user}/{func_name}'
    await async_cache_setex(m_quota_key, 86400 * 7, 100)
    await async_cache_setex(f_quota_key, 86400 * 7, 200)


async def async_main():
    keys = await async_cache_keys('QUOTA*')
    for key in keys:
        print(await async_cache_get(key))
    for key in keys:
        await async_cache_setex(key, 86400 * 7, 0)
    for key in keys:
        print(await async_cache_get(key))


if __name__ == '__main__':
    asyncio.run(test())
    asyncio.run(async_main())
