# 工具函数模块
# 提供各种辅助功能

from typing import List, Tuple, Union, Optional, Callable, Any
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from stockai.state import AgentState, PlanStep
from pydantic import BaseModel


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


def format_messages_for_state(messages: List[AnyMessage], session_id: str = None) -> dict:
    """
    将消息列表格式化为 AgentState 所需的格式
    
    Args:
        messages: agent node 输出的消息列表
        session_id: 会话ID，可选
        
    Returns:
        dict: 包含 conversational_messages 和 messages 的字典
    """
    conversational_messages, all_messages = extract_conversational_messages(messages)
    
    result = {
        "conversaional_messages": conversational_messages,
        "messages": all_messages
    }
    
    if session_id:
        result["session_id"] = session_id
    
    return result


def _get_current_step(state: AgentState, target_node: str) -> Optional[PlanStep]:
    """
    获取当前步骤，如果目标节点匹配则返回步骤对象
    
    Args:
        state: AgentState状态对象
        target_node: 目标节点名称
        
    Returns:
        Optional[PlanStep]: 匹配的步骤对象，如果没有则返回None
    """
    current_plan = state.get("plan", [])
    current_step_index = state.get("current_step_index", 0)
    
    if current_plan and current_step_index < len(current_plan):
        current_step = current_plan[current_step_index]
        if current_step.target_node == target_node:
            return current_step
    
    return None


def get_planner_input(state: AgentState, target_node: str) -> str:
    """
    从状态中获取planner优化的输入，如果没有则返回原始用户输入
    
    Args:
        state: AgentState状态对象
        target_node: 目标节点名称
        
    Returns:
        str: 优化后的输入文本
    """
    current_step = _get_current_step(state, target_node)
    
    # 使用planner优化的输入，如果没有则使用原始用户输入
    return current_step.inputs if current_step else state.get('user_input', '')


def _update_step_status(state: AgentState, target_node: str, status: str, result: str = ""):
    """
    更新步骤状态和结果
    
    Args:
        state: AgentState状态对象
        target_node: 目标节点名称
        status: 新状态
        result: 结果信息
    """
    current_step = _get_current_step(state, target_node)
    if current_step:
        current_step.status = status
        if result:
            current_step.result = result


def _extract_result_from_messages(messages: List[AnyMessage]) -> str:
    """
    从消息列表中提取结果文本
    
    Args:
        messages: 消息列表
        
    Returns:
        str: 提取的结果文本
    """
    if not messages:
        return ""
    
    # 提取最后一个AI消息的内容作为结果
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content
    
    # 如果没有AI消息，返回所有消息的摘要
    return f"生成了{len(messages)}条消息"


def _extract_result_from_output(output: Any) -> Tuple[List[AnyMessage], str]:
    """
    统一从节点输出中提取标准消息列表与用于状态记录的结果文本。

    支持的三类输出：
    1) create_react_agent 输出：{"messages": List[AnyMessage]}
    2) 直接的 AIMessage
    3) 结构化输出(BaseModel) 或 混合输出 {"messages": List[AnyMessage], "structured_response": BaseModel}

    Returns:
        (messages, result_text)
    """
    # 情形3(b)：混合输出（messages + structured_response）优先识别
    if isinstance(output, dict) and "messages" in output and "structured_response" in output and isinstance(output["structured_response"], BaseModel):
        messages: List[AnyMessage] = output.get("messages", [])  # type: ignore
        structured: BaseModel = output["structured_response"]
        # 将结构化数据转成可读文本，包装成 AIMessage 附加到消息尾部
        try:
            data_dict = structured.model_dump()
            content = " | ".join([f"{k}: {v}" for k, v in data_dict.items() if v is not None and v != ""]) if isinstance(data_dict, dict) else str(data_dict)
        except Exception as e:
            content = f"结构化数据解析失败: {str(e)}"
        structured_msg = AIMessage(content=content)
        std_messages = list(messages) + [structured_msg]
        result_text = _extract_result_from_messages(std_messages)
        return std_messages, result_text

    # 情形1：仅 messages 字段
    if isinstance(output, dict) and "messages" in output:
        messages = output["messages"]  # type: ignore
        result_text = _extract_result_from_messages(messages)
        return messages, result_text

    # 情形2：直接 AIMessage
    if isinstance(output, AIMessage):
        return [output], output.content or ""

    # 情形3(a)：纯 BaseModel（LLM 直接 structured_output 返回）
    if isinstance(output, BaseModel):
        try:
            data_dict = output.model_dump()
            content = " | ".join([f"{k}: {v}" for k, v in data_dict.items() if v is not None and v != ""]) if isinstance(data_dict, dict) else str(data_dict)
        except Exception as e:
            content = f"结构化数据解析失败: {str(e)}"
        msg = AIMessage(content=content)
        return [msg], content

    # 其他：转成字符串作为 AIMessage
    content = str(output) if output is not None else ""
    return [AIMessage(content=content)], content


def execute_node_with_error_handling(
    state: AgentState, 
    target_node: str, 
    execute_func: Callable[[], Any]
) -> dict:
    """
    执行节点函数并处理异常，统一管理状态更新
    
    Args:
        state: AgentState状态对象
        target_node: 目标节点名称
        execute_func: 要执行的函数
        
    Returns:
        dict: format_messages_for_state的结果
    """
    session_id = state.get("session_id")
    
    # 更新当前步骤状态为running
    _update_step_status(state, target_node, "running")
    
    # 保存任务开始状态到数据库
    if session_id:
        from .session_manager import session_manager
        current_step = _get_current_step(state, target_node)
        if current_step:
            session_manager.save_task_result(
                session_id=session_id,
                step_id=current_step.id,
                step_description=current_step.description,
                target_node=target_node,
                status="running"
            )
    
    try:
        # 执行节点函数
        raw_output = execute_func()
        
        # 标准化输出（仅在此调用统一提取逻辑）
        messages, result_text = _extract_result_from_output(raw_output)
        
        # 更新步骤状态为 completed，并记录真实结果
        _update_step_status(state, target_node, "completed", result_text)
        
        # 保存任务完成状态到数据库
        if session_id:
            from .session_manager import session_manager
            current_step = _get_current_step(state, target_node)
            if current_step:
                session_manager.save_task_result(
                    session_id=session_id,
                    step_id=current_step.id,
                    step_description=current_step.description,
                    target_node=target_node,
                    result=result_text,
                    status="completed"
                )
        
        # 统一返回标准化的消息格式
        return format_messages_for_state(messages, session_id=session_id)
        
    except Exception as e:
        error_msg = f"执行失败: {str(e)}"
        
        # 更新步骤状态为failed，保存失败原因
        _update_step_status(state, target_node, "failed", error_msg)
        
        # 保存任务失败状态到数据库
        if session_id:
            from .session_manager import session_manager
            current_step = _get_current_step(state, target_node)
            if current_step:
                session_manager.save_task_result(
                    session_id=session_id,
                    step_id=current_step.id,
                    step_description=current_step.description,
                    target_node=target_node,
                    result=error_msg,
                    status="failed",
                    error_message=str(e)
                )
        
        # 将错误信息添加到errors列表
        errors = state.get("errors", [])
        errors.append(f"{target_node}节点执行失败: {str(e)}")
        state["errors"] = errors
        
        return format_messages_for_state([AIMessage(content=f"{target_node}执行失败: {str(e)}")], session_id=session_id)