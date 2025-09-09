# 工具函数模块
# 提供各种辅助功能

from typing import List, Tuple, Union
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage


def extract_conversational_messages(messages: List[AnyMessage]) -> Tuple[List[Union[HumanMessage, AIMessage]], List[AnyMessage]]:
    """
    从 agent node 输出的 messages 列表中提取对话消息和所有消息
    
    Args:
        messages: agent node 输出的消息列表
        
    Returns:
        Tuple[conversational_messages, all_messages]:
        - conversational_messages: 只包含 HumanMessage 和 AIMessage 的对话消息列表
        - all_messages: 包含所有类型消息的完整消息列表
    """
    # 提取对话消息（只包含 HumanMessage 和 AIMessage）
    conversational_messages = []
    for msg in messages:
        if isinstance(msg, (HumanMessage, AIMessage)):
            conversational_messages.append(msg)
    
    # 返回对话消息和所有消息
    return conversational_messages, messages


def format_messages_for_state(messages: List[AnyMessage]) -> dict:
    """
    将消息列表格式化为 AgentState 所需的格式
    
    Args:
        messages: agent node 输出的消息列表
        
    Returns:
        dict: 包含 conversational_messages 和 messages 的字典
    """
    conversational_messages, all_messages = extract_conversational_messages(messages)
    
    return {
        "conversaional_messages": conversational_messages,
        "messages": all_messages
    }