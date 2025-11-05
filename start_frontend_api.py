"""
启动前端 API 服务器
"""

import uvicorn
from api_server import app

if __name__ == "__main__":
    print("🚀 启动 StockAI API 服务器...")
    print("📡 API 地址: http://localhost:8000")
    print("📚 API 文档: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

