
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from stockai.llm import LLM
from stockai.tools.search import baidu_search, get_news_from_eastmoney, get_news_content_from_eastmoney,get_current_time
from stockai.state import AgentState
from stockai.utils import format_messages_for_state

def market_news(state: AgentState):
    system_prompt = f"""
        请根据用户的需求，利用工具分析回答股票相关的问题
        
        # 工具
        - get_current_time
        - get_news_from_eastmoney
        - get_news_content_from_eastmoney
        - baidu_search
        
        # 流程
        - 你应该优先使用get_current_time获得当前时间
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
        tools = [get_current_time,baidu_search, get_news_from_eastmoney, get_news_content_from_eastmoney],
        prompt = system_prompt
        )
    
    result = agent.invoke({'messages': [HumanMessage(content = state.get('user_input'))]})
    
    return format_messages_for_state(result['messages'])
    
