# 会话管理服务
# 提供会话创建、消息保存、任务结果保存等功能

from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from .models import db_manager, Session as SessionModel, Message, TaskResult


class SessionManager:
    """会话管理器 - 负责会话数据的持久化操作"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    def create_session(self, user_id: Optional[str] = None, title: Optional[str] = None) -> str:
        """
        创建新会话
        
        Args:
            user_id: 用户ID，可为空
            title: 会话标题，可为空
            
        Returns:
            str: 新创建的会话ID
        """
        db_session = self.db_manager.get_session()
        try:
            session = SessionModel(
                user_id=user_id,
                title=title or f"会话_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                status='active'
            )
            db_session.add(session)
            db_session.commit()
            return session.id
        except Exception as e:
            db_session.rollback()
            print(f"❌ 创建会话失败: {e}")
            raise
        finally:
            self.db_manager.close_session(db_session)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict: 会话信息，如果不存在返回None
        """
        db_session = self.db_manager.get_session()
        try:
            session = db_session.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session:
                return {
                    'id': session.id,
                    'user_id': session.user_id,
                    'created_at': session.created_at,
                    'updated_at': session.updated_at,
                    'status': session.status,
                    'title': session.title
                }
            return None
        except Exception as e:
            print(f"❌ 获取会话失败: {e}")
            return None
        finally:
            self.db_manager.close_session(db_session)
    
    def save_message(self, session_id: str, role: str, content: str, message_type: str = 'text') -> bool:
        """
        保存消息到数据库
        
        Args:
            session_id: 会话ID
            role: 消息角色 (user, assistant, system)
            content: 消息内容
            message_type: 消息类型 (text, image, file)
            
        Returns:
            bool: 保存是否成功
        """
        db_session = self.db_manager.get_session()
        try:
            message = Message(
                session_id=session_id,
                role=role,
                content=content,
                message_type=message_type
            )
            db_session.add(message)
            db_session.commit()
            return True
        except Exception as e:
            db_session.rollback()
            print(f"❌ 保存消息失败: {e}")
            return False
        finally:
            self.db_manager.close_session(db_session)
    
    def get_session_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取会话的所有消息
        
        Args:
            session_id: 会话ID
            limit: 限制返回数量，None表示不限制
            
        Returns:
            List[Dict]: 消息列表
        """
        db_session = self.db_manager.get_session()
        try:
            query = db_session.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp)
            if limit:
                query = query.limit(limit)
            
            messages = query.all()
            return [
                {
                    'id': msg.id,
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp,
                    'message_type': msg.message_type
                }
                for msg in messages
            ]
        except Exception as e:
            print(f"❌ 获取会话消息失败: {e}")
            return []
        finally:
            self.db_manager.close_session(db_session)
    
    def save_task_result(self, session_id: str, step_id: str, step_description: str = None, 
                        target_node: str = None, result: str = None, status: str = 'pending',
                        error_message: str = None) -> bool:
        """
        保存任务执行结果
        
        Args:
            session_id: 会话ID
            step_id: 步骤ID
            step_description: 步骤描述
            target_node: 目标节点
            result: 执行结果
            status: 状态 (pending, running, completed, failed)
            error_message: 错误信息
            
        Returns:
            bool: 保存是否成功
        """
        db_session = self.db_manager.get_session()
        try:
            # 检查是否已存在该步骤的记录
            existing_task = db_session.query(TaskResult).filter(
                and_(TaskResult.session_id == session_id, TaskResult.step_id == step_id)
            ).first()
            
            if existing_task:
                # 更新现有记录
                existing_task.step_description = step_description or existing_task.step_description
                existing_task.target_node = target_node or existing_task.target_node
                existing_task.result = result or existing_task.result
                existing_task.status = status
                existing_task.error_message = error_message or existing_task.error_message
                if status in ['completed', 'failed']:
                    existing_task.completed_at = datetime.utcnow()
            else:
                # 创建新记录
                task_result = TaskResult(
                    session_id=session_id,
                    step_id=step_id,
                    step_description=step_description,
                    target_node=target_node,
                    result=result,
                    status=status,
                    error_message=error_message
                )
                if status in ['completed', 'failed']:
                    task_result.completed_at = datetime.utcnow()
                db_session.add(task_result)
            
            db_session.commit()
            return True
        except Exception as e:
            db_session.rollback()
            print(f"❌ 保存任务结果失败: {e}")
            return False
        finally:
            self.db_manager.close_session(db_session)
    
    def get_session_tasks(self, session_id: str) -> List[Dict[str, Any]]:
        """
        获取会话的所有任务结果
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[Dict]: 任务结果列表
        """
        db_session = self.db_manager.get_session()
        try:
            tasks = db_session.query(TaskResult).filter(
                TaskResult.session_id == session_id
            ).order_by(TaskResult.created_at).all()
            
            return [
                {
                    'id': task.id,
                    'step_id': task.step_id,
                    'step_description': task.step_description,
                    'target_node': task.target_node,
                    'result': task.result,
                    'status': task.status,
                    'error_message': task.error_message,
                    'created_at': task.created_at,
                    'completed_at': task.completed_at
                }
                for task in tasks
            ]
        except Exception as e:
            print(f"❌ 获取会话任务失败: {e}")
            return []
        finally:
            self.db_manager.close_session(db_session)
    
    def update_session_status(self, session_id: str, status: str, title: str = None) -> bool:
        """
        更新会话状态
        
        Args:
            session_id: 会话ID
            status: 新状态 (active, completed, failed)
            title: 新标题，可选
            
        Returns:
            bool: 更新是否成功
        """
        db_session = self.db_manager.get_session()
        try:
            session = db_session.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session:
                session.status = status
                session.updated_at = datetime.utcnow()
                if title:
                    session.title = title
                db_session.commit()
                return True
            return False
        except Exception as e:
            db_session.rollback()
            print(f"❌ 更新会话状态失败: {e}")
            return False
        finally:
            self.db_manager.close_session(db_session)
    
    def get_user_sessions(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取用户的所有会话
        
        Args:
            user_id: 用户ID
            limit: 限制返回数量
            
        Returns:
            List[Dict]: 会话列表
        """
        db_session = self.db_manager.get_session()
        try:
            sessions = db_session.query(SessionModel).filter(
                SessionModel.user_id == user_id
            ).order_by(desc(SessionModel.updated_at)).limit(limit).all()
            
            return [
                {
                    'id': session.id,
                    'user_id': session.user_id,
                    'created_at': session.created_at,
                    'updated_at': session.updated_at,
                    'status': session.status,
                    'title': session.title
                }
                for session in sessions
            ]
        except Exception as e:
            print(f"❌ 获取用户会话失败: {e}")
            return []
        finally:
            self.db_manager.close_session(db_session)


# 全局会话管理器实例
session_manager = SessionManager()
