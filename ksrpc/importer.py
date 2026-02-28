import importlib
import os
import sys


def import_module_from_path(module_name, file_path):
    """
    从指定文件路径导入模块

    Args:
        module_name (str): 要导入的模块名称（自定义）
        file_path (str): Python 文件的绝对路径

    Returns:
        module: 导入的模块对象
    """
    # 根据文件路径创建模块规格
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"无法从路径 '{file_path}' 创建模块规格")
    # 根据规格创建新的模块对象
    module = importlib.util.module_from_spec(spec)
    # 将模块添加到 sys.modules 全局字典中
    sys.modules[module_name] = module
    # 执行模块代码（加载模块）
    spec.loader.exec_module(module)
    return module


def setenv(key, value):
    """考虑到部分平台不让直接导入os"""
    os.environ[key] = value
