#!/bin/bash
# TechDaily 运行脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "TechDaily - 科技资讯日报"
echo "=========================================="

# 检查 Python3
if ! command -v python3 &> /dev/null; then
    echo "错误: python3 未安装"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo "Python: $PYTHON_VERSION"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo ""
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 检查 activate 文件是否存在且为普通文件
ACTIVATE_FILE="venv/bin/activate"
if [ ! -f "$ACTIVATE_FILE" ]; then
    echo "错误: $ACTIVATE_FILE 不是文件或不存在"
    echo "尝试重新创建虚拟环境..."
    rm -rf venv
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -q feedparser requests pyyaml beautifulsoup4 2>/dev/null || {
    echo "pip 安装失败，尝试使用 python3 -m pip..."
    python3 -m pip install -q feedparser requests pyyaml beautifulsoup4
}

# 运行日报生成
echo ""
echo "运行 TechDaily..."
python3 src/tech_daily.py

# 推送通知（如果配置了）
if [ -f "config/notify_config.json" ]; then
    echo "推送通知..."
    python3 src/notifier.py
fi

echo ""
echo "=========================================="
echo "完成!"
echo "报告位置: output/"
echo "=========================================="
