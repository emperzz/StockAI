#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StockAI前端功能测试脚本
用于验证前端功能是否正常工作
"""

import requests
import time
import json
from datetime import datetime

def test_frontend_availability():
    """测试前端服务是否可用"""
    try:
        response = requests.get("http://localhost:7860", timeout=5)
        if response.status_code == 200:
            print("✅ 前端服务正常运行")
            return True
        else:
            print(f"❌ 前端服务异常，状态码: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到前端服务: {e}")
        return False

def test_stock_data_functions():
    """测试股票数据获取功能"""
    try:
        # 导入我们的模块
        import sys
        import os
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        from my_agent.frontend.gradio_app import get_stock_info, get_stock_data, create_stock_chart
        
        print("\n🔍 测试股票数据获取功能...")
        
        # 测试股票代码
        test_codes = ["000001", "000002", "600000"]
        
        for code in test_codes:
            print(f"\n📊 测试股票代码: {code}")
            
            # 测试基本信息获取
            try:
                info = get_stock_info(code)
                if isinstance(info, str) and "失败" in info:
                    print(f"  ⚠️  基本信息获取失败: {info}")
                else:
                    print(f"  ✅ 基本信息获取成功")
            except Exception as e:
                print(f"  ❌ 基本信息获取异常: {e}")
            
            # 测试历史数据获取
            try:
                data = get_stock_data(code, days=7)
                if isinstance(data, str) and "失败" in data:
                    print(f"  ⚠️  历史数据获取失败: {data}")
                else:
                    print(f"  ✅ 历史数据获取成功，数据量: {len(data)} 条")
                    
                    # 测试图表生成
                    try:
                        chart = create_stock_chart(data)
                        if chart is None:
                            print(f"  ⚠️  图表生成失败")
                        else:
                            print(f"  ✅ 图表生成成功")
                    except Exception as e:
                        print(f"  ❌ 图表生成异常: {e}")
                        
            except Exception as e:
                print(f"  ❌ 历史数据获取异常: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试过程异常: {e}")
        return False

def test_api_endpoints():
    """测试API端点"""
    try:
        print("\n🌐 测试API端点...")
        
        # 测试健康检查
        try:
            response = requests.get("http://localhost:7860/", timeout=5)
            if response.status_code == 200:
                print("  ✅ 主页访问正常")
            else:
                print(f"  ❌ 主页访问异常: {response.status_code}")
        except Exception as e:
            print(f"  ❌ 主页访问失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ API测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 StockAI前端功能测试")
    print("=" * 50)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试前端服务可用性
    if not test_frontend_availability():
        print("\n❌ 前端服务不可用，请先启动服务:")
        print("   conda activate open_manus")
        print("   python start_frontend.py")
        return
    
    # 测试股票数据功能
    test_stock_data_functions()
    
    # 测试API端点
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("🎉 测试完成！")
    print("\n💡 使用说明:")
    print("   1. 打开浏览器访问: http://localhost:7860")
    print("   2. 输入股票代码（如: 000001）")
    print("   3. 点击'分析股票'按钮")
    print("   4. 查看分析结果和K线图")
    print("\n📋 示例股票代码:")
    print("   - 000001: 平安银行")
    print("   - 000002: 万科A")
    print("   - 600000: 浦发银行")
    print("   - 600036: 招商银行")

if __name__ == "__main__":
    main()
