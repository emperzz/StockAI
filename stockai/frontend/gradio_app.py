# Gradio应用
# 定义用户界面和交互逻辑

import gradio as gr
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Tuple, Dict, Any
from stockai.agent import graph
from stockai.state import AgentState

def get_stock_info(stock_code):
    """获取股票基本信息"""
    try:
        # 获取股票基本信息
        stock_info = ak.stock_individual_info_em(symbol=stock_code)
        return stock_info
    except Exception as e:
        return f"获取股票信息失败: {str(e)}"

def get_stock_data(stock_code, period="daily", days=30):
    """获取股票历史数据"""
    try:
        # 获取股票历史数据
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        
        stock_data = ak.stock_zh_a_hist(
            symbol=stock_code, 
            period=period, 
            start_date=start_date, 
            end_date=end_date,
            adjust="qfq"
        )
        return stock_data
    except Exception as e:
        return f"获取股票数据失败: {str(e)}"

def create_stock_chart(stock_data):
    """创建股票K线图"""
    if isinstance(stock_data, str):  # 如果是错误信息
        return None
    
    try:
        # 创建K线图
        fig = go.Figure(data=go.Candlestick(
            x=stock_data['日期'],
            open=stock_data['开盘'],
            high=stock_data['最高'],
            low=stock_data['最低'],
            close=stock_data['收盘']
        ))
        
        fig.update_layout(
            title='股票K线图',
            xaxis_title='日期',
            yaxis_title='价格',
            template='plotly_dark'
        )
        
        return fig
    except Exception as e:
        return None

def analyze_stock(stock_code):
    """分析股票数据"""
    try:
        # 获取股票数据
        stock_data = get_stock_data(stock_code, days=60)
        
        if isinstance(stock_data, str):  # 如果是错误信息
            return stock_data, None, None
        
        # 获取股票基本信息
        stock_info = get_stock_info(stock_code)
        
        # 创建图表
        chart = create_stock_chart(stock_data)
        
        # 计算基本统计信息
        latest_price = stock_data['收盘'].iloc[-1]
        price_change = stock_data['收盘'].iloc[-1] - stock_data['收盘'].iloc[-2]
        price_change_pct = (price_change / stock_data['收盘'].iloc[-2]) * 100
        
        # 格式化输出
        analysis_text = f"""
## 股票分析结果

**股票代码**: {stock_code}
**最新价格**: {latest_price:.2f} 元
**涨跌额**: {price_change:+.2f} 元
**涨跌幅**: {price_change_pct:+.2f}%

### 基本信息
{stock_info.to_string() if hasattr(stock_info, 'to_string') else str(stock_info)}

### 数据统计
- 数据期间: {stock_data['日期'].min()} 至 {stock_data['日期'].max()}
- 最高价: {stock_data['最高'].max():.2f} 元
- 最低价: {stock_data['最低'].min():.2f} 元
- 平均成交量: {stock_data['成交量'].mean():.0f}
        """
        
        return analysis_text, stock_data, chart
        
    except Exception as e:
        return f"分析失败: {str(e)}", None, None


def chat_with_agent(user_message: str, chat_history: List[Tuple[str, str]]):
    """与LangGraph Agent对话，返回更新后的历史记录和清空后的输入。

    - 不影响现有分析功能
    - 使用后端graph，默认返回hello
    """
    try:
        if user_message is None:
            user_message = ""

        # 将历史转换为简单的role/content结构，供后续扩展使用
        converted_history: List[Dict[str, str]] = []
        for user, bot in chat_history or []:
            if user:
                converted_history.append({"role": "user", "content": user})
            if bot:
                converted_history.append({"role": "assistant", "content": bot})

        initial_state: AgentState = {
            "user_input": user_message,
            "response": "",
            "error": None,
            "status": "processing",
            "conversation_history": converted_history,
        }

        result: Dict[str, Any] = graph.invoke(initial_state)
        bot_reply: str = result.get("response", "")

        updated_history = (chat_history or []) + [(user_message, bot_reply)]
        return updated_history, ""
    except Exception as e:
        updated_history = (chat_history or []) + [(user_message or "", f"对话出错: {e}")]
        return updated_history, ""

# 创建Gradio界面
def create_gradio_app():
    """创建Gradio应用界面"""
    
    with gr.Blocks(
        title="StockAI - 中国股市AI分析系统",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1200px !important;
        }
        """
    ) as app:
        
        gr.Markdown("""
        # 🚀 StockAI - 中国股市AI分析系统
        
        欢迎使用StockAI！这是一个基于AI的中国股市分析系统，可以帮助您：
        - 📊 获取实时股票数据
        - 📈 生成股票K线图
        - 🔍 进行基础技术分析
        - 🤖 AI智能分析（即将推出）
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📝 输入股票代码")
                stock_code_input = gr.Textbox(
                    label="股票代码",
                    placeholder="例如: 000001 (平安银行)",
                    value="000001"
                )
                
                analyze_btn = gr.Button("🔍 分析股票", variant="primary", size="lg")
                
                gr.Markdown("""
                ### 💡 使用说明
                - 输入6位股票代码（如：000001）
                - 点击"分析股票"按钮
                - 查看分析结果和图表
                
                ### 📋 示例代码
                - 000001: 平安银行
                - 000002: 万科A
                - 600000: 浦发银行
                - 600036: 招商银行
                """)
            
            with gr.Column(scale=4):
                gr.Markdown("### 📊 分析结果")
                
                # 分析结果输出
                analysis_output = gr.Markdown(label="分析结果")
                
                # 数据表格
                data_table = gr.Dataframe(
                    label="股票数据",
                    headers=["日期", "开盘", "收盘", "最高", "最低", "成交量", "成交额"],
                    interactive=False
                )
                
                # 图表显示
                chart_output = gr.Plot(label="K线图")

        # 分割线
        gr.Markdown("---")

        # 新增：对话能力（不影响现有分析模块）
        gr.Markdown("### 💬 对话助手（LangGraph）")
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(height=300, label="对话历史")
                with gr.Row():
                    chat_input = gr.Textbox(
                        label="输入消息",
                        placeholder="和StockAI助手对话（当前为固定hello回复）",
                        scale=8
                    )
                    send_btn = gr.Button("发送", variant="primary", scale=1)

                # 回车发送
                chat_input.submit(
                    fn=chat_with_agent,
                    inputs=[chat_input, chatbot],
                    outputs=[chatbot, chat_input]
                )
                # 点击发送
                send_btn.click(
                    fn=chat_with_agent,
                    inputs=[chat_input, chatbot],
                    outputs=[chatbot, chat_input]
                )
        
        # 绑定事件
        analyze_btn.click(
            fn=analyze_stock,
            inputs=[stock_code_input],
            outputs=[analysis_output, data_table, chart_output]
        )
        
        # 示例按钮
        gr.Markdown("### 🎯 快速测试")
        with gr.Row():
            gr.Button("测试 000001").click(
                fn=lambda: "000001",
                outputs=[stock_code_input]
            )
            gr.Button("测试 000002").click(
                fn=lambda: "000002", 
                outputs=[stock_code_input]
            )
            gr.Button("测试 600000").click(
                fn=lambda: "600000",
                outputs=[stock_code_input]
            )
    
    return app

# 主函数
def main():
    """启动Gradio应用"""
    app = create_gradio_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True
    )

if __name__ == "__main__":
    main()
