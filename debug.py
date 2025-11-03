from langchain_core.messages import HumanMessage
from stockai.agent import graph
from IPython.display import Image, display

from adapters.akshare_adapter import AKShareAdapter
import pandas as pd
from adapters.myquant_adapters import MyQuantAdapter

md = MyQuantAdapter()
# md.get_historical_prices('SZSE:000001', start_date = pd.to_datetime('2025-10-31'), end_date = pd.to_datetime('2025-11-01'), interval = '1d')

ak = AKShareAdapter()
# ak.get_real_time_market('SSE')
ak.get_real_time_price('SZSE:000001')
# ak.get_historical_prices('SSE:600219', start_date = pd.to_datetime('2025-10-30'), end_date = pd.to_datetime('2025-10-31'), interval = '1d')


# display(Image(graph.get_graph(xray = True).draw_mermaid_png()))
result = graph.invoke({'user_input': '帮我分析下上证指数的走势'})   

