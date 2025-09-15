from langchain_core.messages import HumanMessage
from stockai.agent import graph
from IPython.display import Image, display

# display(Image(graph.get_graph(xray = True).draw_mermaid_png()))

result = graph.invoke({'user_input': '帮我分析下上证指数的走势'})