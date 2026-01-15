#!/bin/bash
# 启动脚本 - 自动激活虚拟环境并运行服务

cd "$(dirname "$0")"

echo "=========================================="
echo "  中医体质判定 API 服务"
echo "=========================================="
echo ""

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，正在创建..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
    echo ""
    echo "正在安装依赖..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ 依赖安装完成"
    echo ""
fi

# 激活虚拟环境
source venv/bin/activate

echo "🚀 正在启动服务..."
echo ""
echo "📍 API 文档地址: http://localhost:8000/docs"
echo "📍 健康检查: http://localhost:8000/health"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="
echo ""

# 启动服务
python main.py
