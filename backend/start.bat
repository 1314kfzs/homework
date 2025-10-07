@echo off
echo 启动 ArXiv RAG 后端服务...

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 安装依赖包...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --prefer-binary

REM 创建数据目录
if not exist "data" mkdir data

REM 启动服务
echo 启动后端服务 (端口 8001)...
python run.py

pause