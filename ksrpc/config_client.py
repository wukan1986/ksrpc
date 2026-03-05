import os

# 打印下载进度条
PRINT_PROGRESS: int = int(os.getenv("PRINT_PROGRESS", 1))
# 2, 底层自动跳转，可支持多次重定向。至少发送了2次请求+1次数据请求。启动速度慢一些
# 1, 手工跳转，只支持一次重定向。发送了1次请求+1次数据请求。启动速度快一些
# 0, 直连。遇到重定向会报错，发送了1次数据请求。启动速度更快。确信不会出现重定向才使用此功能
HTTP_ALLOW_REDIRECTS: int = int(os.getenv("HTTP_ALLOW_REDIRECTS", 1))

print("__file__:", __file__)
print("PRINT_PROGRESS:", PRINT_PROGRESS)
print("HTTP_ALLOW_REDIRECTS:", HTTP_ALLOW_REDIRECTS)
