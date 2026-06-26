#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechDaily 本地HTTP服务器
用于托管报告文件，供企业微信/钉钉访问
"""

import http.server
import socketserver
import socket
from pathlib import Path
import sys

# 配置
PORT = 8080
SERVE_DIR = Path(__file__).parent.parent / "output"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SERVE_DIR), **kwargs)

    def log_message(self, format, *args):
        # 简化日志输出
        print(f"[HTTP] {self.address_string()} - {format % args}")

def get_local_ip():
    """获取本机局域网IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def start_server(port=PORT, background=False):
    """启动HTTP服务器"""
    if not SERVE_DIR.exists():
        SERVE_DIR.mkdir(parents=True, exist_ok=True)

    handler = MyHTTPRequestHandler

    with socketserver.TCPServer(("0.0.0.0", port), handler) as httpd:
        local_ip = get_local_ip()
        print(f"=" * 60)
        print(f"TechDaily HTTP Server Started")
        print(f"=" * 60)
        print(f"Local URL:  http://127.0.0.1:{port}/")
        print(f"LAN URL:    http://{local_ip}:{port}/")
        print(f"Report:     http://{local_ip}:{port}/latest.html")
        print(f"Directory:  {SERVE_DIR}")
        print(f"=" * 60)
        print(f"Press Ctrl+C to stop")
        print(f"=" * 60)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TechDaily HTTP Server")
    parser.add_argument("-p", "--port", type=int, default=PORT, help=f"Port (default: {PORT})")
    parser.add_argument("-b", "--background", action="store_true", help="Run in background")
    args = parser.parse_args()

    start_server(args.port, args.background)
