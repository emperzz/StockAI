
from typing import List
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from stockai.llm import LLM
from stockai.tools.search import baidu_search, get_news_from_eastmoney, get_news_content_from_eastmoney,get_current_time
from stockai.tools.akshare import get_concept_list,get_concept_realtime_data, get_concept_kline, get_concept_detail,get_limitup_stocks_by_date
from stockai.tools.analysis import analyze_concepts_overlap
from stockai.state import AgentState
from stockai.utils import format_messages_for_state

def market_news(state: AgentState):
        
    
    system_prompt = f"""
        ---
        当前时间: {get_current_time()}
        ---
        请根据用户的需求，利用工具分析回答股票相关的问题
        
        # 工具
        - get_news_from_eastmoney
        - get_news_content_from_eastmoney
        - baidu_search
        
        # 流程
        - 然后使用get_news_from_eastmoney工具，获取东方财富网的新闻
        - 请根据新闻内容从中挑选出有助于判断上涨原因的新闻
        - 若新闻内容中的信息欠缺细节，可以使用get_news_content_from_eastmoney传入url列表提取完整的新闻内容
        - 如果以上两个工具依然找不到合适的消息，你可以使用baidu_search工具，搜索其他网站的新闻
        
        # 注意
        - 离当前时间越近的消息对当前走势的影响越大
        - 除非近期（1周内）找不到有效的消息，再考虑扩大消息查询的时间范围
        - 一切的判断都以你查询到的信息为准，不要自己创造任何信息
        - 如果实在找不到合适的消息，请直接回复不知道
        
        """



    agent = create_react_agent(
        model = LLM().get_model(),
        tools = [baidu_search, get_news_from_eastmoney, get_news_content_from_eastmoney],
        prompt = system_prompt
        )
    
    result = agent.invoke({'messages': [HumanMessage(content = state.get('user_input'))]})
    
    return format_messages_for_state(result['messages'])
    


def get_proper_concept(state: AgentState):
    
    class Concept(BaseModel):
        code: str = Field(..., description = '板块的代码')
        name: str = Field(..., description = '板块的名称')
        reason: str = Field(..., description = '选择板块的原因')
        
    class LLMOutput(BaseModel):
        concept_list : List[Concept] = Field(..., description = '选取的板块列表')
        content: str = Field(..., description = '选择板块的思考过程，如果没有合适的板块，也同样解释原因')
    
    system_prompt = f"""
    ---
    当前时间: {get_current_time()}
    ---
    请根据要求提取合适的板块清单
    
    # 工具
    - get_concept_list: 获取最新的板块清单
    - get_concept_realtime_data: 获取最新的板块清单和数据
    - get_concept_kline : 获取板块的K线数据
    - analyze_concepts_overlap : 根据传入的板块代码列表，分析两两板块配对的股票重叠度
    - get_concept_detail :  获取指定板块的成分股明细，涨停情况与统计。
    
    # 要求
    - 根据用户的要求提取出相应的板块名称
    - 如果用户没有明确要求，则提取涨幅在前20的板块即可
    - 除非特殊声明，否则排除名字里带有'昨日'的板块
    - 如果实在没有合适的板块，请回复原因，并返回空的列表
    
    ## 选股
    - 如果挑选板块的目的是为了从板块中挑选出合适的标的，除非用户特别说明，否则你应该使用analyze_concepts_overlap来排除重复率较高的板块
    - 挑选的板块理想的情况下，应该有3只涨停股票，或1只20%涨停，1只10%涨停的股票。你可以通过get_concept_detail获取板块的最新涨停情况
    - 如果当天大盘不好，可选板块不足，你可以降低标准，但板块最少要有1只涨停的股票
    - 板块当日的涨幅必须为正
    - 尽量选择板块内股票数量充足的板块
    
    """
    
    agent = create_react_agent(
        model = LLM().get_model(),
        tools = [get_concept_list,get_concept_realtime_data, get_concept_kline,analyze_concepts_overlap,get_concept_detail],
        prompt = system_prompt,
        # response_format = LLMOutput
        )
    
    result = agent.invoke({'messages': [HumanMessage(content = state.get('user_input'))]})
    
    return format_messages_for_state(result['messages'])


def analyze_reason(state: AgentState):
    pass

def analyze_leading_stocks(state: AgentState):
    system_prompt = f"""
    ---
    当前时间: {get_current_time()}
    ---
    请根据提供给你的板块内的股票数据，提取龙头股和权重股
    
    # 工具
    - get_concept_detail:  获取指定板块的成分股明细，涨停情况与统计。
    - get_limitup_stocks_by_date: 获取全部涨停的股票
    
    
    # 要求
    ## 龙头股
    - 龙头股一定是涨停的股票，不涨停不能算龙头
    - 如果涨停的股票数量大于等于3只，则挑选3只龙头股股票，按照重要程度排序。如果小于3只，则有几只返回几只，如果没有涨停的股票，则返回空列表
    - 如果涨停股票不足3个，则挑选所有涨停的股票并按照下面的排序规则排序后输出
    - 连板的股票比首次涨停的股票更符合龙头股，连板次数越多，重要程度越高
    - 同样涨停幅度内，先涨停（最后涨停时间）的比后涨停的重要程度高
    - 同样涨停次数的股票（包括），20%涨停的股票比30%涨停的重要程度高, 30%的比10%的重要程度高
    - 差不多同时涨停的股票，市值大的比市值小的股票重要程度高
    
    ## 其他
    - 如果没有限制板块，就从市场所有的涨停股中挑选市场总龙头
    - 如果有限制板块，则从需求的板块中挑选
    - 如果用户一次性提供了好几个板块，你则按循序依次挑选
    """
    
    agent = create_react_agent(
        model = LLM().get_model(),
        tools = [get_limitup_stocks_by_date, get_concept_detail],
        prompt = system_prompt,
        # response_format = LLMOutput
        )
    
    result = agent.invoke({'messages': [HumanMessage(content = state.get('user_input'))]})
    
    return format_messages_for_state(result['messages'])