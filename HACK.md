# 一些小工具

## 1. 读取源代码

```python
# 1. 如果可以执行命令
# !cat /opt/conda/lib/python3.6/site-packages/xxx.py

# 2. 如果支持open打开文件
import xxx

with open(xxx.__file__, "r") as f:
    print(f.read())

# 2. 如果支持pandas打开文件
import pandas as pd

df = pd.read_csv('/opt/conda/lib/python3.6/site-packages/xxx.py',
                 engine='python', header=None, encoding='utf-8',
                 sep='\r', skip_blank_lines=False, doublequote=False)

print(df.to_csv(index=None, header=None, quotechar='\1').replace('\1', ''))

```

## 写入源文件

```python
import pandas as pd

df = pd.DataFrame(
    [
        "import os as os_",
        "import sys as sys_",
        "eval_ = eval",
        "open_ = open",
        "get_ipython_ = get_ipython",
        "exec_ = get_ipython().ex",
        "os_open_ = os_.open",
        "import ctypes",
        "import_ = __import__",
        "from IPython.core.interactiveshell import InteractiveShell",
        "InteractiveShell.ast_transformers = []",
    ])

print(df.to_csv(index=None, header=None, sep="$"))
df.to_csv('a.py', index=None, header=None, sep="$")
```

## 安装自定义包
```python
try:
    from pip import main as pipmain
except:
    from pip._internal import main as pipmain

pipmain(['install', '--target', '/home/user/mylib', 'pandas'])
```

## 完整示例
```python
from pip import main as pipmain
pipmain(['install', '--target', '/home/jovyan/work/mylib', 'ksrpc', '-i', "https://mirrors.aliyun.com/pypi/simple"])


import collections
collections._sys.path.append('/home/jovyan/work/mylib')

_os = collections._sys.modules['os']


env = _os.environ
env['PYTHONPATH'] = '/home/jovyan/work/mylib:$PYTHONPATH'

_os.system("chmod 777 frpc")

```