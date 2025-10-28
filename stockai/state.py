# 状态定义
# 定义LangGraph工作流的状态结构

from typing import Annotated, TypedDict, List, Optional, Sequence, Union, Dict, Any, Literal
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.graph import StateGraph, add_messages
from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    """计划步骤定义"""
    id: str = Field(..., description="步骤唯一标识")
    description: str = Field(..., description="步骤描述")
    target_node: str = Field(..., description="目标节点名称")
    inputs: str = Field(..., description="传递给目标节点的需求文本")
    result: str = Field(default="", description="目标节点的处理结果")
    status: Literal["pending", "running", "completed", "failed"] = Field(default="pending", description="步骤状态")


class AgentState(TypedDict):
    """Agent状态定义"""
    # 用户输入
    user_input: str
    # 历史对话
    conversaional_messages: Annotated[Sequence[Union[HumanMessage, AIMessage]], add_messages]
    # Agent的所有messages
    messages: Annotated[Sequence[AnyMessage], add_messages]
    # Planner相关字段
    plan: List[PlanStep]  # 任务计划
    current_step_index: int  # 当前步骤索引
    artifacts: Dict[str, Any]  # 中间产物存储
    errors: List[str]  # 错误信息
    # 会话管理字段
    session_id: Optional[str]  # 会话ID，用于数据持久化
