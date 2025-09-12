"""
HTTP服务+frp反代

在某宽上FastAPI 服务可以开启，但客户端连接失败，问题出在uvicorn
通过测试，python -m http.server 能运行，所以决定重写这部分

这次的功能非常简单，只为在某容器中提供HTTP服务，其他权限认证等功能全去除

"""
import os
import socketserver
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import cgi  # https://pypi.org/project/legacy-cgi/

from ksrpc.caller_simple import simple_call
from ksrpc.config import PORT, HOST
from ksrpc.serializer.pkl_gzip import deserialize


class FileHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Hello, this is a simple API!")
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Endpoint not found")

    def do_POST(self):
        if self.path.startswith('/api/file'):
            parsed_path = urlparse(self.path)
            query_params = parse_qs(parsed_path.query)
            func = query_params['func'][0]

            # Parse the form data posted
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type'], }
            )
            file = form['file'].file.read()

            key, buf, data = simple_call(func, **deserialize(file))

            # Begin the response
            self.send_response(200)
            self.send_header("content-type", 'application/octet-stream')
            self.send_header("content-disposition", f'attachment; filename="{key}.pkl.gz"')
            self.end_headers()
            self.wfile.write(buf)
            return


if hasattr(os, "fork"):
    TCPServer = socketserver.ForkingTCPServer
else:
    TCPServer = socketserver.ThreadingTCPServer


def main():
    with TCPServer((HOST, PORT), FileHTTPRequestHandler) as server:
        print(f"Serving on port {PORT}")
        server.serve_forever()
