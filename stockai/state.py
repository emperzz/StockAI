# 状态定义
# 定义LangGraph工作流的状态结构

from typing import Annotated, TypedDict, List, Optional, Sequence
from langchain_core.messages import AnyMessage
from langgraph.graph import StateGraph, add_messages


class AgentState(TypedDict):
    """Agent状态定义"""
    # 用户输入
    user_input: AnyMessage
    # 历史对话
    messages: Annotated[Sequence[AnyMessage], add_messages]
