import math


def format_number(speed_bps, units=['', 'K', 'M', 'G']):
    """
    将网速（单位：B/s）格式化为更易读的字符串，并可选添加颜色。

    参数:
        speed_bps (float): 以字节每秒（B/s）为单位的网速。
        use_color (bool): 是否使用ANSI颜色代码美化输出（适用于终端）。

    返回:
        str: 格式化后的网速字符串，如"1.23 MB/s"或带颜色的字符串。
    """
    # 计算合适的单位索引：通过对数确定应使用的单位级别
    if speed_bps <= 0:
        index = 0
    else:
        index = min(int(math.log(speed_bps, 1024)), len(units) - 1)  # 限制索引不超过单位列表长度

    # 转换速度值
    speed_converted = speed_bps / (1024 ** index)

    # 动态格式化：根据单位调整小数位数（单位越小，显示更多小数位以提高精度）
    if index == 0:  # B/s
        formatted_speed = f"{speed_converted:.2f}"
    elif index == 1:  # KB/s
        formatted_speed = f"{speed_converted:.2f}"
    else:  # MB/s或更大单位
        formatted_speed = f"{speed_converted:.2f}"

    # 构建结果字符串
    result = f"{formatted_speed}{units[index]}"
    return result
