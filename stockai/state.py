# 状态定义
# 定义LangGraph工作流的状态结构

from typing import Annotated, TypedDict, List, Optional, Sequence, Union
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.graph import StateGraph, add_messages


class AgentState(TypedDict):
    """Agent状态定义"""
    # 用户输入
    user_input: str
    # 历史对话
    conversaional_messages: Annotated[Sequence[Union[HumanMessage, AIMessage]], add_messages]
    # Agent的所有messages
    messages: Annotated[Sequence[AnyMessage], add_messages]
