# LangGraph工作流定义
# 包含图的构建和节点定义

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from my_agent.state import AgentState


def hello_node(state: AgentState) -> Dict[str, Any]:
    """
    基础回答节点 - 默认回复hello
    不需要调用大语言模型，直接返回固定回复
    """
    print(f"收到用户输入: {state['user_input']}")
    
    # 更新状态
    return {
        "response": "Hello! 我是StockAI助手，很高兴为您服务！",
        "status": "completed",
        "error": None
    }


def should_continue(state: AgentState) -> str:
    """
    决定是否继续处理的条件函数
    """
    if state.get("status") == "error":
        return "error"
    return "end"


def error_node(state: AgentState) -> Dict[str, Any]:
    """
    错误处理节点
    """
    return {
        "response": f"抱歉，处理过程中出现错误: {state.get('error', '未知错误')}",
        "status": "error"
    }


# 构建LangGraph工作流
def create_graph() -> StateGraph:
    """
    创建LangGraph工作流图
    """
    # 创建状态图
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("hello", hello_node)
    workflow.add_node("error_handler", error_node)
    
    # 设置入口点
    workflow.set_entry_point("hello")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "hello",
        should_continue,
        {
            "end": END,
            "error": "error_handler"
        }
    )
    
    # 错误节点直接结束
    workflow.add_edge("error_handler", END)
    
    return workflow


# 创建图实例
graph = create_graph().compile()
