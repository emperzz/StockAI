# 数据库模型定义
# 用于会话数据和任务结果的持久化存储

from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import Config
import uuid

Base = declarative_base()


class Session(Base):
    """会话表 - 存储会话基本信息"""
    __tablename__ = 'sessions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=True, comment="用户ID，可为空")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    status = Column(String(20), default='active', comment="会话状态：active, completed, failed")
    title = Column(String(200), nullable=True, comment="会话标题")
    
    # 关联关系
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    task_results = relationship("TaskResult", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    """消息表 - 存储对话消息"""
    __tablename__ = 'messages'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey('sessions.id'), nullable=False, comment="会话ID")
    role = Column(String(20), nullable=False, comment="消息角色：user, assistant, system")
    content = Column(Text, nullable=False, comment="消息内容")
    timestamp = Column(DateTime, default=datetime.utcnow, comment="消息时间")
    message_type = Column(String(20), default='text', comment="消息类型：text, image, file")
    
    # 关联关系
    session = relationship("Session", back_populates="messages")


class TaskResult(Base):
    """任务结果表 - 存储任务执行结果"""
    __tablename__ = 'task_results'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey('sessions.id'), nullable=False, comment="会话ID")
    step_id = Column(String(100), nullable=False, comment="步骤ID")
    step_description = Column(String(500), nullable=True, comment="步骤描述")
    target_node = Column(String(100), nullable=True, comment="目标节点")
    result = Column(Text, nullable=True, comment="执行结果")
    status = Column(String(20), nullable=False, comment="状态：pending, running, completed, failed")
    error_message = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    
    # 关联关系
    session = relationship("Session", back_populates="task_results")


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.config = Config()
        self.engine = None
        self.SessionLocal = None
        self._init_database()
    
    def _init_database(self):
        """初始化数据库连接"""
        try:
            # 使用config.py中的数据库配置
            database_url = self.config.SQLALCHEMY_DATABASE_URI
            self.engine = create_engine(database_url, echo=False)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # 创建所有表
            Base.metadata.create_all(bind=self.engine)
            print(f"✅ 数据库初始化成功: {database_url}")
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            raise
    
    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()
    
    def close_session(self, session):
        """关闭数据库会话"""
        if session:
            session.close()


# 全局数据库管理器实例
db_manager = DatabaseManager()
