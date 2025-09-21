import time  # noqa

"""
TODO Basic认证。一定要修改账号，不要使用默认值
"""
USER_CREDENTIALS = {
    "用户名": "密码",
    "admin": "password123",
    "user": "secret",
}


def check_url_path(path):
    """TODO 为防路径扫描，这里可以使用其他路径。甚至可以搞规则判断。多条规则，只能留一条
    """
    # 1.因为本项目是模拟HTTP文件上传和下载，为反映其特点，所以约定file
    assert path == 'file', "未授权路径"
    # 2. 客户端与服务端时间差不能超过10秒
    # assert abs(time.time() - int(path)) < 10, "时间误差大"



