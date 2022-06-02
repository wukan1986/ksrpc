def check_ip(ip_list, ip, default):
    """IP检查

    找到了，就用约定的值
    没找到，就用默认值default
    """
    for x, y in ip_list.items():
        # if IP(ip) in IP(x):
        if ip in x:
            # 返回指定值
            return y
    # 没找到，反回默认值
    return default


def check_methods(dict_, list_, default):
    """方法权限检查

    找到了，就用约定的值
    没找到，就用默认值default
    """
    d = dict_
    for x in list_:
        d = d.get(x, default)
        if isinstance(d, bool):
            return d
    return default


def get_quota(dict_, list_, default):
    """方法权限检查

    找到了，就用约定的值
    没找到，就用默认值default
    """
    d = dict_
    for x in list_:
        d = d.get(x, default)
        if isinstance(d, int):
            return d
    return default


if __name__ == "__main__":
    from IPy import IP

    IP_ALLOW = {
        IP('127.0.0.0/8'): True,  # 回环地址
        IP('192.168.0.0/16'): True,  # C类内网
        IP('172.16.0.0/12'): True,  # B类内网
        IP('10.0.0.0/8'): True,  # A类内网
    }
    IP_BLOCK = {
        IP('8.8.8.8/32'): False,
        IP('8.8.4.4/32'): False,
    }
    print(check_ip(IP_ALLOW, IP('127.0.0.1'), False))
    print(check_ip(IP_ALLOW, IP('172.31.0.0'), False))
    print(check_ip(IP_ALLOW, IP('114.114.114.114'), False))
    print(check_ip(IP_BLOCK, IP('8.8.8.8'), True))
    print(check_ip(IP_BLOCK, IP('114.114.114.114'), True))
