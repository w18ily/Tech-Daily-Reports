#!/bin/bash
# TechDaily 启动脚本
# 用法: bash start.sh [port]

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${1:-8080}"

echo "=========================================="
echo "TechDaily 启动器"
echo "=========================================="

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: python3 未安装"
    exit 1
fi

# 安装依赖
echo "检查依赖..."
python3 -m pip install --user feedparser requests pyyaml beautifulsoup4 -q 2>/dev/null || true

# 启动HTTP服务器（后台）
echo ""
echo "启动HTTP服务器 (端口: $PORT)..."
nohup python3 src/web_server.py -p "$PORT" > output/server.log 2>&1 &
SERVER_PID=$!
echo "服务器PID: $SERVER_PID"

# 等待服务器启动
sleep 2

# 获取IP
LOCAL_IP=$(python3 -c "import socket; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(('8.8.8.8',80)); print(s.getsockname()[0]); s.close()")
echo "报告访问地址: http://${LOCAL_IP}:${PORT}/latest.html"
echo ""

# 运行日报生成（会自动推送）
echo "运行日报生成..."
python3 src/tech_daily.py

echo ""
echo "=========================================="
echo "完成!"
echo "报告: http://${LOCAL_IP}:${PORT}/latest.html"
echo "日志: output/server.log"
echo "停止服务器: kill $SERVER_PID"
echo "=========================================="
