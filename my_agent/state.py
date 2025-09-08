# 状态定义
# 定义LangGraph工作流的状态结构

from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph


class AgentState(TypedDict):
    """Agent状态定义"""
    # 用户输入
    user_input: str
    
    # 处理结果
    response: str
    
    # 错误信息
    error: Optional[str]
    
    # 处理状态
    status: str  # "processing", "completed", "error"
    
    # 历史对话
    conversation_history: List[dict]
