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
from adapters.myquant_adapters import MyQuantAdapter
from adapters.types import AssetPrice

def get_stock_info(stock_code):
    """获取股票基本信息"""
    try:
        # 支持传入 "SSE:600000" 或 "SZSE:000001" 格式
        symbol = stock_code.split(":", 1)[1] if ":" in str(stock_code) else stock_code
        stock_info = ak.stock_individual_info_em(symbol=symbol)
        return stock_info
    except Exception as e:
        return f"获取股票信息失败: {str(e)}"

_myquant_adapter: MyQuantAdapter | None = None


def _get_adapter() -> MyQuantAdapter:
    global _myquant_adapter
    if _myquant_adapter is None:
        _myquant_adapter = MyQuantAdapter()
    return _myquant_adapter


def _prices_to_df(prices: List[AssetPrice]) -> pd.DataFrame:
    if not prices:
        return pd.DataFrame(columns=["日期", "开盘", "收盘", "最高", "最低", "成交量", "成交额"]) 
    rows = []
    for p in prices:
        close_val = float(p.close_price) if p.close_price is not None else (float(p.price) if p.price is not None else None)
        open_val = float(p.open_price) if p.open_price is not None else None
        high_val = float(p.high_price) if p.high_price is not None else None
        low_val = float(p.low_price) if p.low_price is not None else None
        vol_val = float(p.volume) if p.volume is not None else None
        amt_val = float(p.amount) if p.amount is not None else None
        rows.append({
            "日期": p.timestamp,
            "开盘": open_val,
            "收盘": close_val,
            "最高": high_val,
            "最低": low_val,
            "成交量": vol_val,
            "成交额": amt_val,
        })
    df = pd.DataFrame(rows)
    df.sort_values(by="日期", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def get_stock_data(stock_code: str, interval: str = "1d", days: int = 30):
    """使用 MyQuantAdapter 获取历史数据（单只）
    interval: "1d" or "1m"
    - 1m: 仅获取今日的1分钟数据
    - 1d: 获取最近 days 天（默认用于多股票图，可设置为365）
    """
    try:
        adapter = _get_adapter()
        now = datetime.now()
        if interval == "1m":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        else:
            start_date = now - timedelta(days=days)
            end_date = now

        prices = adapter.get_historical_prices(
            ticker=stock_code,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
        )
        return _prices_to_df(prices)
    except Exception as e:
        return f"获取股票数据失败: {str(e)}"


def get_multi_stock_data(stock_codes: List[str], interval: str = "1d", days: int = 30) -> Dict[str, Any]:
    """获取多只股票历史数据，返回 {code: DataFrame 或 错误字符串} 映射"""
    results: Dict[str, Any] = {}
    for code in stock_codes:
        code = code.strip()
        if not code:
            continue
        results[code] = get_stock_data(code, interval=interval, days=days)
    return results

def create_return_line_chart(stock_data_map: Dict[str, Any]):
    """创建多只股票的涨跌幅折线图（首个点归一为0%）"""
    try:
        records: List[Dict[str, Any]] = []
        for code, df in stock_data_map.items():
            if isinstance(df, str) or df is None:
                continue
            if df.empty or '收盘' not in df.columns:
                continue
            series = (df['收盘'] / df['收盘'].iloc[0] - 1.0) * 100.0
            tmp = pd.DataFrame({
                '日期': df['日期'],
                '涨跌幅%': series,
                '股票代码': code,
            })
            records.append(tmp)
        if not records:
            return None
        plot_df = pd.concat(records, ignore_index=True)
        fig = px.line(plot_df, x='日期', y='涨跌幅%', color='股票代码', title='多股票相对涨跌幅（首日=0%）')
        fig.update_layout(template='plotly_dark', yaxis_title='涨跌幅（%）', xaxis_title='日期')
        return fig
    except Exception:
        return None

def analyze_stock(stock_code_input: str, interval: str):
    """分析股票数据，支持以","或"，"分隔的多股票输入。
    - analysis_output 与 data_table 仅展示第一只股票
    - chart 展示多只股票的涨跌幅折线图（首个点=0%）
    """
    try:
        if stock_code_input is None:
            stock_code_input = ""
        # 解析多股票输入
        raw_codes = [c.strip() for c in stock_code_input.replace('，', ',').split(',') if c.strip()]
        if not raw_codes:
            return "请输入至少一只股票代码", None, None

        first_code = raw_codes[0]

        # 获取第一只股票数据用于分析与表格
        days = 365 if interval == "1d" else 1
        first_df = get_stock_data(first_code, interval=interval, days=days)
        if isinstance(first_df, str):
            return first_df, None, None

        # 多股票数据用于图表
        multi_map = get_multi_stock_data(raw_codes, interval=interval, days=days)
        chart = create_return_line_chart(multi_map)

        # 基本信息与统计基于第一只股票
        stock_info = get_stock_info(first_code)
        latest_price = first_df['收盘'].iloc[-1]
        if len(first_df) >= 2:
            price_change = first_df['收盘'].iloc[-1] - first_df['收盘'].iloc[-2]
            price_change_pct = (price_change / first_df['收盘'].iloc[-2]) * 100
        else:
            price_change = 0.0
            price_change_pct = 0.0

        analysis_text = f"""
## 股票分析结果

**股票代码**: {first_code}
**最新价格**: {latest_price:.2f} 元
**涨跌额**: {price_change:+.2f} 元
**涨跌幅**: {price_change_pct:+.2f}%

### 基本信息
{stock_info.to_string() if hasattr(stock_info, 'to_string') else str(stock_info)}

### 数据统计
- 数据期间: {first_df['日期'].min()} 至 {first_df['日期'].max()}
- 最高价: {first_df['最高'].max():.2f} 元
- 最低价: {first_df['最低'].min():.2f} 元
- 平均成交量: {first_df['成交量'].mean() if '成交量' in first_df.columns and not first_df['成交量'].isna().all() else 0:.0f}
        """

        return analysis_text, first_df, chart

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
                    placeholder="支持多只，用逗号分隔。例如: SZSE:000001,SSE:600036",
                    value="SZSE:000001"
                )
                interval_input = gr.Dropdown(
                    label="Interval",
                    choices=["1d", "1m"],
                    value="1d"
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
            inputs=[stock_code_input, interval_input],
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
