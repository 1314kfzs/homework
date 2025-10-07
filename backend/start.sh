#!/bin/bash

echo "启动 ArXiv RAG 后端服务..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装依赖包..."
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --prefer-binary

# 创建数据目录
mkdir -p data

# 启动服务
echo "启动后端服务 (端口 8001)..."
python run.py