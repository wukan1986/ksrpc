import setuptools

with open("README.md", "r", encoding='utf-8') as fp:
    long_description = fp.read()

version = {}
with open("ksrpc/_version.py", encoding="utf-8") as fp:
    exec(fp.read(), version)

setuptools.setup(
    name="ksrpc",
    version=version['__version__'],
    author="wukan",
    author_email="wu-kan@163.com",
    description="Keep Simple RPC",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wukan1986/ksrpc",
    packages=setuptools.find_packages(),
    # 默认。用于支持反弹RPC
    install_requires=[
        'loguru',
        'nest-asyncio',
        'pandas',
        'pydantic',
        'websockets',
    ],
    extras_require={
        # 服务端
        'server': [
            'aioredis',
            'fakeredis',
            'fastapi',
            'python-multipart',
            'uvicorn[standard]',
            'IPy',
        ],
        # 客户端
        'client': [
            'httpx',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Intended Audience :: Developers',
    ],
    python_requires=">=3.6",
)
