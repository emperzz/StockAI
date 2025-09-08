# LangGraph工作流定义
# 包含图的构建和节点定义

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from stockai.state import AgentState
from stockai.llm import LLM


def hello_node(state: AgentState) -> Dict[str, Any]:
    """
    使用已配置的 LLM 模型对用户输入进行一次简单回复。
    """
    user_input = state.get("user_input")
    text = getattr(user_input, "content", str(user_input))

    model = LLM().get_model()
    messages = [
        SystemMessage(content="你是StockAI智能助手，请用简洁中文回答。"),
        HumanMessage(content=text or "你好")
    ]
    ai_msg = model.invoke(messages)

    return {
        "messages": [ai_msg]
    }


def should_continue(state: AgentState) -> str:
    """
    简化后的流转：hello 节点后直接结束。
    """
    return "end"


def error_node(state: AgentState) -> Dict[str, Any]:
    """
    兼容保留（不再使用）。
    """
    return {"response": ""}


# 构建LangGraph工作流
def create_graph() -> StateGraph:
    """
    创建LangGraph工作流图
    """
    # 创建状态图
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("hello", hello_node)
    
    # 设置入口点
    workflow.set_entry_point("hello")
    
    # 添加条件边：hello -> END
    workflow.add_conditional_edges(
        "hello",
        should_continue,
        {"end": END}
    )
    
    return workflow


# 创建图实例
graph = create_graph().compile()
