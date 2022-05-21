from functools import reduce


def ip_into_int(ip):
    # 先把 192.168.1.13 变成16进制的 c0.a8.01.0d ，再去了“.”后转成10进制的 3232235789 即可。
    # (((((192 * 256) + 168) * 256) + 1) * 256) + 13
    return reduce(lambda x, y: (x << 8) + y, map(int, ip.split('.')))


_net_a = ip_into_int('10.255.255.255') >> 24
_net_b = ip_into_int('172.31.255.255') >> 20
_net_c = ip_into_int('192.168.255.255') >> 16
_net_lookback = ip_into_int('127.0.0.0') >> 24


def is_internal_ip(ip):
    """是否内网地址"""
    ip = ip_into_int(ip)
    return (ip >> 24 == _net_a) or (ip >> 20 == _net_b) or (ip >> 16 == _net_c)


def is_lookback_ip(ip):
    """是否回环地址"""
    ip = ip_into_int(ip)
    return ip >> 24 == _net_lookback


def in_whitelist(ip):
    """检查地址是否合法

    如果部署在外网，可以设置白名单
    """
    ip = ip_into_int(ip)
    return (ip >> 24 == _net_lookback) or (ip >> 16 == _net_c) or (ip >> 24 == _net_a) or (ip >> 20 == _net_b)
