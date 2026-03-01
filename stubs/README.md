# 存根文件(.pyi)如何使用

`rpc`项目动态调用的远程库，如果能在`IDE`中能实现语法提示将极大的方便开发。我们可以利用存根文件来解决

## 生成ksrpc的存根文件

可以在自己的新项目中执行以下命令

```bash
uv pip install mypy
# 生成RpcClient对应的存根文件
uv run stubgen -p ksrpc.client -o ./stubs # 只生成一个文件，需要补`__init__.pyi`
# 或
uv run stubgen -p ksrpc -o ./stubs # 全包生成
```

## 生成对应目标库的存根文件(此处以`uuid`库为例)

```bash
uv run stubgen -p uuid -o ./stubs
```

将`uuid.pyi`文件中的部分函数代码复制到`client.piy`文件的`RpcClient`类下，并添加`self`，例如：

```python
class RpcClient:
    def collect(self): ...

    def generate_stub(self): ...

    def __iter__(self): ...

    def __aiter__(self): ...

    # 以下从uuid.pyi中复制过来的，然后加了self
    def uuid4(self): ...

    def uuid5(self, namespace, name): ...
```

最重要一步!!!在`client.pyi`同文件夹建一个`__init__.pyi`，否则`IDE`自动补全无法生效

## PyCharm设置

`stubs`文件夹，`Mark directory as`->`Sources Root`
或
`File->Settings->Project->Project Structure`进行`Sources`设置

## VSCode设置

1. 创建 `.vscode/settings.json`文件
2. 添加以下内容

```json
{
  "python.analysis.stubPath": "stubs"
}
```

## 如果服务器上无权限执行`stubgen`命令怎么办？

本项目提供了`generate_stub`函数，可自行将输出保存。再人工调整。参考`demo_stubs.py`文件

服务器上安装请使用`pip install ksrpc[stub]`

它还有一大好处是可用于探索远程模块所支持的函数