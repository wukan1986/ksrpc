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

将`uuid.pyi`文件中的部分函数代码复制到`client.piy`文件的`RpcClient`类下，并添加`self`,

最重要一步!!!在`client.pyi`同文件夹建一个`__init__.pyi`，否则`IDE`自动补全无法生效

## PyCharm设置

`stubs`文件夹，`Mark directory as`->`Sources Root`
或
`File->Settings->Project->Project Structure`进行`Sources`设置

## 服务器上无法执行`stubgen`命令

本项目提供了`generate_stub`，将输出保存。再人工调整。参考`demo_stubs.py`文件