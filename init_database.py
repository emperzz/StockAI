#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建会话管理相关的数据库表
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from stockai.models import db_manager, Base
from config import Config

def init_database():
    """初始化数据库表"""
    try:
        print("🚀 开始初始化数据库...")
        
        # 获取数据库配置
        config = Config()
        database_url = config.SQLALCHEMY_DATABASE_URI
        print(f"📊 数据库URL: {database_url}")
        
        # 创建所有表
        Base.metadata.create_all(bind=db_manager.engine)
        
        print("✅ 数据库表创建成功！")
        print("📋 已创建的表:")
        print("   - sessions (会话表)")
        print("   - messages (消息表)")
        print("   - task_results (任务结果表)")
        
        # 测试数据库连接
        session = db_manager.get_session()
        try:
            # 测试查询
            from stockai.models import Session
            count = session.query(Session).count()
            print(f"🔍 测试查询成功，当前会话数量: {count}")
        except Exception as e:
            print(f"⚠️ 测试查询失败: {e}")
        finally:
            db_manager.close_session(session)
            
        print("🎉 数据库初始化完成！")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)

def check_database_status():
    """检查数据库状态"""
    try:
        print("🔍 检查数据库状态...")
        
        session = db_manager.get_session()
        try:
            from stockai.models import Session, Message, TaskResult
            
            # 统计各表记录数
            session_count = session.query(Session).count()
            message_count = session.query(Message).count()
            task_count = session.query(TaskResult).count()
            
            print(f"📊 数据库状态:")
            print(f"   - 会话数量: {session_count}")
            print(f"   - 消息数量: {message_count}")
            print(f"   - 任务数量: {task_count}")
            
        except Exception as e:
            print(f"❌ 检查数据库状态失败: {e}")
        finally:
            db_manager.close_session(session)
            
    except Exception as e:
        print(f"❌ 无法连接到数据库: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库管理工具")
    parser.add_argument("--init", action="store_true", help="初始化数据库")
    parser.add_argument("--status", action="store_true", help="检查数据库状态")
    
    args = parser.parse_args()
    
    if args.init:
        init_database()
    elif args.status:
        check_database_status()
    else:
        print("请使用 --init 初始化数据库或 --status 检查状态")
        print("示例:")
        print("  python init_database.py --init")
        print("  python init_database.py --status")
