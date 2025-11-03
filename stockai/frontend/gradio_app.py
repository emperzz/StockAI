# Gradio应用
# 定义用户界面和交互逻辑

import gradio as gr
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Tuple, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
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

    适配最新的 AgentState（仅包含 user_input 与 messages），并基于 agent 返回的
    messages 提取最新的助手回复。
    """
    try:
        if user_message is None:
            user_message = ""

        # 将历史记录转换为 LangChain 消息序列
        history_messages: List[Any] = []
        for user, bot in chat_history or []:
            if user:
                history_messages.append(HumanMessage(content=user))
            if bot:
                history_messages.append(AIMessage(content=bot))

        current_user_msg = HumanMessage(content=user_message)
        messages = history_messages + [current_user_msg]

        initial_state: AgentState = {
            "user_input": current_user_msg,
            "messages": messages,
        }

        result: Dict[str, Any] = graph.invoke(initial_state)
        result_messages = result.get("messages", []) or []

        # 从返回的消息中找到最后一条助手回复（放宽匹配：取最后一个非 HumanMessage 的消息）
        bot_reply = ""
        for m in reversed(result_messages):
            try:
                msg_content = getattr(m, "content", None)
                if not msg_content:
                    continue
                # 优先匹配 AIMessage
                if isinstance(m, AIMessage):
                    bot_reply = msg_content
                    break
                # 兼容其他消息实现：跳过 HumanMessage，保留其它类型
                if isinstance(m, HumanMessage):
                    continue
                msg_type = getattr(m, "type", None)
                if msg_type and str(msg_type).lower() == "human":
                    continue
                bot_reply = msg_content
                break
            except Exception:
                continue

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
        /* 让容器占满整个屏幕宽高 */
        html, body, #root { height: 100%; }
        body { margin: 0; }
        .gradio-container {
            max-width: 100% !important;   /* 宽度铺满 */
            min-height: 100vh !important; /* 高度铺满 */
            padding: 0 16px;              /* 轻量内边距，避免贴边 */
        }
        
        /* 让主要行容器（包含3列的行）高度占满屏幕 */
        .gradio-container > div > div > div[row].svelte-1xp0cw7,
        .gradio-container > div > div > div[class*="row"] {
            min-height: calc(100vh - 140px) !important;
            height: calc(100vh - 140px) !important;
        }
        
        /* 让分析结果列（flex-grow: 6）和对话助手列（flex-grow: 4）高度占满 */
        .gradio-container .column[style*="flex-grow: 6"],
        .gradio-container .column[style*="flex-grow: 4"] {
            display: flex !important;
            flex-direction: column !important;
            height: 100% !important;
            min-height: calc(100vh - 140px) !important;
        }
        
        /* 让Chatbot区域自动填充剩余空间 */
        .gradio-container .column[style*="flex-grow: 4"] div[class*="bubble-wrap"] {
            flex: 1 1 auto !important;
            min-height: 400px !important;
            max-height: none !important;
        }
        
        /* 隐藏"输入消息"标签 - 通过label=""已经移除，这里做双重保险 */
        .gradio-container .column[style*="flex-grow: 4"] label[data-testid="block-info"],
        .gradio-container .column[style*="flex-grow: 4"] span[data-testid="block-info"] {
            display: none !important;
            visibility: hidden !important;
        }
        
        /* 让发送按钮和输入框在同一行且高度一致 */
        .gradio-container .column[style*="flex-grow: 4"] .row:last-child {
            align-items: stretch !important;
            display: flex !important;
        }
        
        /* 让输入框占满容器，缩小发送按钮 */
        .gradio-container .column[style*="flex-grow: 4"] .row:last-child {
            gap: 8px !important;
        }
        
        /* 针对包含textarea和button的行 - 让输入框占满，缩小按钮 */
        .gradio-container .column[style*="flex-grow: 4"] .row:last-child label.svelte-1ae7ssi {
            flex: 1 1 auto !important;
            min-width: 0 !important;
        }
        
        .gradio-container .column[style*="flex-grow: 4"] .row:last-child textarea {
            width: 100% !important;
            min-height: 42px !important;
            height: 42px !important;
            box-sizing: border-box !important;
            resize: vertical !important;
        }
        
        .gradio-container .column[style*="flex-grow: 4"] .row:last-child button {
            min-height: 42px !important;
            height: 42px !important;
            flex: 0 0 70px !important;
            min-width: 70px !important;
            max-width: 70px !important;
            width: 70px !important;
            box-sizing: border-box !important;
        }
        
        /* 移除"股票代码"标签的空白布局 - 选择股票代码标签所在的block容器 */
        .gradio-container .column[style*="flex-grow: 2"] div.block[id="component-5"],
        .gradio-container .column[style*="flex-grow: 2"] div.block[id*="component-5"] {
            padding: 0 !important;
            margin: 0 0 4px 0 !important;
            background: transparent !important;
            border: none !important;
            min-width: auto !important;
            overflow: visible !important;
        }
        
        /* 确保标签文本样式正确 */
        .gradio-container .column[style*="flex-grow: 2"] div.block[id*="component-5"] {
            display: block !important;
        }
        
        /* 缩小"分析股票"按钮的高度 */
        .gradio-container .column[style*="flex-grow: 2"] button[id*="component-6"] {
            height: 40px !important;
            min-height: 40px !important;
            padding: 8px 16px !important;
        }
        """
    ) as app:

        gr.Markdown("""
        # 🚀 StockAI - 中国股市AI分析系统
        """)
        
        with gr.Row(equal_height=True):
            with gr.Column(scale=2, min_width=280):
                gr.Markdown("### 📝 输入股票代码", max_height = 30)
                stock_code_input = gr.Textbox(
                    label="股票代码",
                    placeholder="例如: 000001 (平安银行)",
                    value="000001"
                )
                
                analyze_btn = gr.Button("🔍 分析股票", variant="primary", size="sm")
                
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
            
            with gr.Column(scale=6):
                gr.Markdown("### 📊 分析结果")
                
                # 分析结果输出
                analysis_output = gr.Markdown(label="分析结果", max_height = 30)
                
                # 数据表格
                data_table = gr.Dataframe(
                    label="股票数据",
                    headers=["日期", "开盘", "收盘", "最高", "最低", "成交量", "成交额"],
                    interactive=False
                )
                
                # 图表显示
                chart_output = gr.Plot(label="K线图")

            # 右侧：对话助手
            with gr.Column(scale=4, min_width=360):
                gr.Markdown("### 💬 对话助手（LangGraph）", max_height = 30)
                chatbot = gr.Chatbot(label="对话历史", height=600)
                with gr.Row():
                    chat_input = gr.Textbox(
                        label="",  # 移除标签
                        placeholder="和StockAI助手对话（当前为固定hello回复）",
                        scale=9,
                        container=False
                    )
                    send_btn = gr.Button("发送", variant="primary", scale=1, size="sm")

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
    
    return app

# 主函数
def main():
    """启动Gradio应用
    
    启用 autoreload=True 后，当修改代码文件时，Gradio 会自动检测并重新加载应用。
    无需手动重启服务器。
    """
    app = create_gradio_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True
    )

if __name__ == "__main__":
    main()
