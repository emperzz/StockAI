from datetime import datetime, timedelta
from typing import Annotated, List, Literal, Optional, Sequence, TypedDict
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command, Send
from stockai.tools.akshare import (
    get_current_time, 
    get_index_kline, get_concept_kline, get_stock_kline,
    get_index_list,get_concept_list,get_stock_list
    )
from stockai.utils import format_messages_for_state, get_planner_input, execute_node_with_error_handling
from stockai.llm import LLM
# 从state.py导入状态定义
from stockai.state import AgentState
from stockai.session_manager import session_manager



def trend_analyze(state: AgentState) :
    
    # 使用共用函数获取planner优化的输入
    user_input = get_planner_input(state, "trend_analyze")
    session_id = state.get("session_id")
    
    def _execute_trend_analysis():
        """执行趋势分析的核心逻辑"""
        system_prompt = f"""
        ---
        当前时间: {get_current_time()}
        ---
        请根据用户的需求，利用工具进行股票的走势情况分析
        
        # 工具
        ## 时间
        - get_current_time
        ## 股票清单
        - get_index_list: 获取沪深股市的重要指数列表
        - get_concept_list：获取板块列表
        - get_stock_list ：获取所有股票列表
        ## 行情数据
        - get_index_kline ：获取指数行情数据
        - get_concept_kline ：获取板块行情数据
        - get_stock_kline ：获取个股行情数据
        
        ## 说明
        - 如果用户没有提供给你需要分析的目的代码或名称，你需要自行调用工具获取
        - get_stock_list会获取超过5000条股票的数据，非必要不要使用，你应该根据用户的需求先缩小筛选范围，提取板块，在从板块中查找股票
        - 针对列表获取，优先选用markdown作为获得的数据格式，减少token占用
        - 针对行情数据，选择你最易于理解的数据格式[dict, markdown, json], 如果你要查询大量的K线数据，如1年的日线数据，在不影响你的数据理解的情况下，尽量使用markdown减少token调用
        - get_concept_kline：需要传入的是板块的名称而不是代码。
        
        # 一般分析流程
        - 使用prefix_kline(period = 'weekly') 提取最近1年的K线数据用以分析长期趋势
        - 使用prefix_kline(start_date = today - 7 days(eg. 2025-09-07), period = 'daily'), 提取最近7天的日线数据，分析最近的趋势情况
        - 使用prefix_kiline(, period = '5', start_date = today(eg. 2025-09-12), **kwargs)
        - 除非特殊要求，在分析分时数据时，使用不小于5分钟级别（period = '5'）的分时数据
        

        # 分析要求
        ## 总体趋势
        - 只基于获得的走势数据做分析，不要自行做假设
        - 用文字详细的描述数据时间内的走势趋势，使得其他人可以通过文字就了解到详细的走势情况
        - 除了走势，还要注意量价关系，不同的走势里，对应的成交量是什么样的
        - 目前价格距离最近的压力位和支撑位有多远。
        ## 最近走势
        - 详细分析最近几天的走势情况，对应的量价关系如何
        ## 分时数据
        - 你应该提取最新的1分钟分时数据，分析分时数据的趋势情况
        - 一天的1分钟数据应该有240行，如果你收到的数据不足240行，可能是由于当天的时间还未到收盘，请根据已提供的数据分析
        - 分时数据你除了需要关注趋势外，还需要重点关注最高价和最大成交量的时间，是否有连续的放量上升或下跌成交
        - 重点关注量价（成交和走势的关系），如上涨时是否有对应的放量，量能如何。上涨是波次性的还是持续性的等等
        
        # 注意
        - 如果用户的需求中有明确查询到行情数据级别，请根据用户的需求调用工具，如仅分析日线的趋势和走势，或仅分析分时数据
        - 只基于数据做分析，不要自行做假设
        - 用文字详细的描述数据时间内的走势趋势，使得其他人可以通过文字就了解到详细的走势情况
        
        """
        
        llm = LLM().get_model()
        
        agent = create_react_agent(
            model = llm,
            tools = [get_index_kline, get_concept_kline, get_stock_kline,
                     get_index_list,get_concept_list,get_stock_list],
            prompt = system_prompt
        )
        
        result = agent.invoke({'messages': [HumanMessage(content = user_input)]})
        return format_messages_for_state(result['messages'])
    
    # 使用公共异常处理函数
    return execute_node_with_error_handling(
        state=state,
        target_node="trend_analyze",
        execute_func=_execute_trend_analysis
    )
    

