#!/usr/bin/env python3
"""
ArXiv RAG 后端服务启动脚本
"""

import uvicorn
from main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=True,  # 开发模式热重载
        log_level="info"
    )