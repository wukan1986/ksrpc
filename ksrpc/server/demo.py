"""
演示函数
"""
import asyncio
import random
import time

import numpy as np


def sync_say_hi(name):
    n = random.randint(1, 3)
    time.sleep(n)
    return f'Hello {name}'


async def async_say_hi(name):
    n = random.randint(1, 3)
    await asyncio.sleep(n)
    return f'Hello {name}'


def div(a, b):
    return a / b


def test():
    import pandas as pd
    df = pd.DataFrame({'A': [1, 2, 3, 4, 5]})
    return df


def create_1d_array(target_mb: int = 100):
    """
    创建指定内存大小的一维 NumPy 数组

    参数:
    target_mb -- 目标内存大小 (MB)，默认为 100MB
    dtype -- 数组数据类型，默认为 np.float64

    返回:
    ndarray -- 创建的 NumPy 一维数组
    """
    dtype = np.float64
    # 计算目标字节数
    target_bytes = target_mb * 1024 * 1024

    # 获取数据类型大小
    element_size = np.dtype(dtype).itemsize

    # 计算所需元素数量
    num_elements = target_bytes // element_size

    # 创建随机数组
    arr = np.random.rand(num_elements).astype(dtype)

    # 验证并打印结果
    actual_mb = arr.nbytes / (1024 * 1024)
    print(f"创建成功: {actual_mb:.2f} MB 一维数组")
    print(f"数据类型: {arr.dtype}")
    print(f"元素数量: {arr.size:,}")

    return arr


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __format__(self, format_spec):
        # 如果没有提供格式说明符或为空，使用默认表示
        if format_spec == "":
            return f"({self.x}, {self.y})"
        # 根据不同的格式说明符返回不同的格式
        elif format_spec == "c":
            return f"({self.x}, {self.y})"
        elif format_spec == "p":
            return f"Point({self.x}, {self.y})"
        elif format_spec == "r":  # 例如，保留两位小数
            return f"({round(self.x, 2)}, {round(self.y, 2)})"
        else:
            # 对于无法识别的格式说明符，可以返回默认表示或抛出异常
            return f"({self.x}, {self.y})"


# 使用示例
p = Point(3.14159, 2.71828)


def test_array():
    arr = create_1d_array()
    return arr[:100]


PASSWORD = 123456
LIST = [1, 2, 3, 4, 5]


class A:
    class B:
        C = [11, 22, 33, 44, 55]

    D = B


CLASS = A


def sync_counter():
    n = 1
    while n <= 3:
        yield n
        n += 1

async def async_counter():
    n = 1
    while n <= 3:
        yield n
        n += 1