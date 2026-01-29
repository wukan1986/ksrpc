"""
DNS SRV模式，配置方便，Lucky软件中，直接配置即可

但，SRV模式，DNS缓存中记录的地址可能已经过期，需要多次获取，而302重定向没有这个问题

302重定向最大的问题是webhook配置不容易

"""
from urllib.parse import urlparse

import requests

response = requests.get("https://www.baidu.com", allow_redirects=False)
# 获取最终的 URL（可能经过重定向）
final_url = response.next.url
parsed_url = urlparse(final_url)
port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
print(parsed_url.hostname, port)

toml = """
serverAddr = "{target}"
serverPort = {port}
auth.token = "frp.example.com"

[[proxies]]
name = "aaaa"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8080
remotePort = 7001

"""

toml = toml.format(target=parsed_url.hostname, port=port)
print(toml)

with open("frpc.toml", 'w', encoding='utf-8') as f:
    f.write(toml)
