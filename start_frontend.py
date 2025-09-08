#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StockAI前端启动脚本
用于启动Gradio前端界面
"""

import sys
import os

# 添加项目路径到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 导入并启动前端应用
from my_agent.frontend.gradio_app import main

if __name__ == "__main__":
    print("🚀 正在启动StockAI前端界面...")
    print("📱 界面将在 http://localhost:7860 打开")
    print("⏹️  按 Ctrl+C 停止服务")
    print("-" * 50)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("💡 请确保已安装所有依赖: pip install -r my_agent/requirements.txt")
