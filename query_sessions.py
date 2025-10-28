#!/usr/bin/env python3
"""
会话查询工具
用于查询和管理会话数据
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from stockai.session_manager import session_manager

def list_sessions(limit=10):
    """列出最近的会话"""
    try:
        print(f"📋 最近 {limit} 个会话:")
        print("-" * 80)
        
        # 这里需要修改为获取所有会话，因为当前没有按时间排序的方法
        # 暂时使用空字符串作为user_id来获取所有会话
        sessions = session_manager.get_user_sessions("", limit)
        
        if not sessions:
            print("📭 没有找到任何会话")
            return
        
        for i, session in enumerate(sessions, 1):
            print(f"{i:2d}. ID: {session['id']}")
            print(f"    标题: {session['title']}")
            print(f"    状态: {session['status']}")
            print(f"    创建时间: {session['created_at']}")
            print(f"    更新时间: {session['updated_at']}")
            print()
            
    except Exception as e:
        print(f"❌ 查询会话失败: {e}")

def show_session_detail(session_id):
    """显示会话详情"""
    try:
        print(f"🔍 会话详情: {session_id}")
        print("=" * 80)
        
        # 获取会话信息
        session_info = session_manager.get_session(session_id)
        if not session_info:
            print("❌ 会话不存在")
            return
        
        print(f"📋 会话信息:")
        print(f"   ID: {session_info['id']}")
        print(f"   标题: {session_info['title']}")
        print(f"   状态: {session_info['status']}")
        print(f"   创建时间: {session_info['created_at']}")
        print(f"   更新时间: {session_info['updated_at']}")
        print()
        
        # 获取消息历史
        messages = session_manager.get_session_messages(session_id)
        print(f"💬 消息历史 ({len(messages)} 条):")
        print("-" * 40)
        for msg in messages:
            role_icon = "👤" if msg['role'] == 'user' else "🤖"
            print(f"{role_icon} [{msg['role']}] {msg['timestamp']}")
            print(f"   {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}")
            print()
        
        # 获取任务结果
        tasks = session_manager.get_session_tasks(session_id)
        print(f"📊 任务结果 ({len(tasks)} 个):")
        print("-" * 40)
        for task in tasks:
            status_icon = "✅" if task['status'] == 'completed' else "❌" if task['status'] == 'failed' else "⏳"
            print(f"{status_icon} [{task['status']}] {task['step_description']}")
            if task['result']:
                print(f"   结果: {task['result'][:100]}{'...' if len(task['result']) > 100 else ''}")
            if task['error_message']:
                print(f"   错误: {task['error_message']}")
            print()
            
    except Exception as e:
        print(f"❌ 查询会话详情失败: {e}")

def search_sessions(keyword):
    """搜索会话"""
    try:
        print(f"🔍 搜索关键词: {keyword}")
        print("-" * 80)
        
        # 这里可以实现更复杂的搜索逻辑
        # 暂时简单列出所有会话，然后过滤
        sessions = session_manager.get_user_sessions("", 100)
        
        filtered_sessions = []
        for session in sessions:
            if keyword.lower() in session['title'].lower():
                filtered_sessions.append(session)
        
        if not filtered_sessions:
            print("📭 没有找到匹配的会话")
            return
        
        print(f"📋 找到 {len(filtered_sessions)} 个匹配的会话:")
        for i, session in enumerate(filtered_sessions, 1):
            print(f"{i:2d}. {session['title']} ({session['id']})")
            print(f"    状态: {session['status']} | 创建时间: {session['created_at']}")
            print()
            
    except Exception as e:
        print(f"❌ 搜索会话失败: {e}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="会话查询工具")
    parser.add_argument("--list", "-l", type=int, metavar="N", help="列出最近N个会话")
    parser.add_argument("--show", "-s", metavar="SESSION_ID", help="显示指定会话详情")
    parser.add_argument("--search", metavar="KEYWORD", help="搜索会话")
    
    args = parser.parse_args()
    
    if args.list:
        list_sessions(args.list)
    elif args.show:
        show_session_detail(args.show)
    elif args.search:
        search_sessions(args.search)
    else:
        print("会话查询工具")
        print("=" * 40)
        print("用法:")
        print("  python query_sessions.py --list 10          # 列出最近10个会话")
        print("  python query_sessions.py --show SESSION_ID  # 显示会话详情")
        print("  python query_sessions.py --search 关键词    # 搜索会话")
        print()
        print("示例:")
        print("  python query_sessions.py --list 5")
        print("  python query_sessions.py --show abc123-def456-ghi789")
        print("  python query_sessions.py --search 股票分析")

if __name__ == "__main__":
    main()
