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



def trend_analyze(state: AgentState) :
    
    # 使用共用函数获取planner优化的输入
    user_input = get_planner_input(state, "trend_analyze")
    
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
        - 针对行情数据，选择你最易于理解的数据格式[dict, markdown, json]
        - get_concept_kline：需要传入的是板块的名称而不是代码。
        
        # 要求
        - 尽量不要一次性获取太多的数据
        - 如果需要分析年度的趋势，你可以按周提取k线数据
        - 针对某一段时期的趋势，如最近一周，你可以按日提取K线数据分析
        - 1分钟级的数据一次不要提取超过1天的数据
        

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
        - 分时数据你去了需要关注趋势外，还需要重点关注最高价和最大成交量的时间，是否有连续的放量上升或下跌成交
        
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
    

