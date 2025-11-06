"""
FastAPI 后端服务
将 Python 功能暴露为 REST API，供前端调用
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入 gradio_app 中的函数
from stockai.frontend.gradio_app import (
    get_multi_stock_data,
    create_return_line_chart,
    analyze_stock,
    chat_with_agent,
)
from adapters.myquant_adapters import MyQuantAdapter

app = FastAPI(title="StockAI API", version="1.0.0")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求模型
class AnalyzeStockRequest(BaseModel):
    stock_code: str
    interval: str = "1d"


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = None


# 响应模型
class StockDataResponse(BaseModel):
    日期: str
    开盘: Optional[float] = None
    收盘: Optional[float] = None
    最高: Optional[float] = None
    最低: Optional[float] = None
    成交量: Optional[float] = None
    成交额: Optional[float] = None


class StockChartData(BaseModel):
    dates: List[str]
    stocks: List[Dict[str, Any]]


class StockAnalysisResponse(BaseModel):
    analysis_text: str
    data_table: List[StockDataResponse]
    chart_data: Optional[StockChartData] = None


class ChatResponse(BaseModel):
    message: str


@app.get("/")
async def root():
    return {"message": "StockAI API Server"}


@app.get("/api/market/quotes")
async def get_market_quotes(tickers: Optional[str] = None):
    """
    通用实时行情接口：支持股票 / 指数 / 板块。

    - 参数 tickers: 逗号分隔的内部代码（internal_ticker），如 "SSE:000001,SZSE:399001"
    - 若不传，则返回常用指数：上证、深证成指、创业板指、沪深300
    返回字段：name, code(不含交易所前缀), price, change, pct
    """
    try:
        adapter = MyQuantAdapter()

        # 解析 tickers 参数（必须提供 internal_ticker，如 SSE:000001）
        if not (tickers and isinstance(tickers, str)):
            raise HTTPException(status_code=400, detail="缺少必须的参数: tickers，例如 SSE:000001,SZSE:399001")
        # 去重并保持顺序
        req_tickers = []
        for t in tickers.split(","):
            t = t.strip()
            if t and t not in req_tickers:
                req_tickers.append(t)
        ticker_name_pairs = [(t, None) for t in req_tickers]

        results = []
        for ticker, preset_name in ticker_name_pairs:
            try:
                rt = adapter.get_real_time_price(ticker)
                if rt is None:
                    continue
                # 兼容返回列表的情况，取最后一条
                if isinstance(rt, list):
                    if not rt:
                        continue
                    rt = rt[-1]

                # 价格
                if getattr(rt, 'price', None) is not None:
                    price_val = float(rt.price)
                elif getattr(rt, 'close_price', None) is not None:
                    price_val = float(rt.close_price)
                else:
                    price_val = 0.0

                # 涨跌与涨跌幅（已知适配器提供 change 与 change_pct）
                change_val = float(rt.change) if getattr(rt, 'change', None) is not None else 0.0
                pct_attr = 'change_pct' if getattr(rt, 'change_pct', None) is not None else (
                    'change_percent' if getattr(rt, 'change_percent', None) is not None else None
                )
                pct_val = float(getattr(rt, pct_attr)) if pct_attr else 0.0

                # 名称：优先使用预设；否则尝试资产信息
                name_val = preset_name
                if not name_val:
                    try:
                        asset = adapter.get_asset_info(ticker)
                        if asset is not None and getattr(asset, 'name', None):
                            name_val = str(asset.name)
                    except Exception:
                        pass

                results.append({
                    "name": name_val or ticker,
                    "code": ticker.split(":", 1)[1] if ":" in ticker else ticker,
                    "price": round(price_val, 2),
                    "change": round(change_val, 2),
                    "pct": round(pct_val, 2),
                })
            except Exception:
                continue
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实时数据失败: {str(e)}")


@app.get("/api/stock/info/{stock_code}")
async def get_stock_info_api(stock_code: str):
    """获取股票基本信息"""
    try:
        adapter = MyQuantAdapter()

        def normalize_ticker(code: str) -> str:
            if ":" in code:
                return code
            code = code.strip()
            if code.startswith("6"):
                return f"SSE:{code}"
            return f"SZSE:{code}"

        ticker = normalize_ticker(stock_code)
        asset = adapter.get_asset_info(ticker)
        if asset is None:
            raise HTTPException(status_code=404, detail=f"未找到股票信息: {stock_code}")

        return asset.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票信息失败: {str(e)}")


@app.get("/api/stock/data/{stock_code}")
async def get_stock_data_api(stock_code: str, interval: str = "1d", days: int = 30):
    """获取股票历史数据"""
    try:
        from datetime import datetime, timedelta

        adapter = MyQuantAdapter()

        def normalize_ticker(code: str) -> str:
            if ":" in code:
                return code
            code = code.strip()
            if code.startswith("6"):
                return f"SSE:{code}"
            return f"SZSE:{code}"

        ticker = normalize_ticker(stock_code)

        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days)

        prices = adapter.get_historical_prices(ticker=ticker, start_date=start_dt, end_date=end_dt, interval=interval)

        def to_row(p):
            try:
                return {
                    "日期": p.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "开盘": float(p.open_price) if p.open_price is not None else None,
                    "收盘": float(p.close_price) if p.close_price is not None else (float(p.price) if p.price is not None else None),
                    "最高": float(p.high_price) if p.high_price is not None else None,
                    "最低": float(p.low_price) if p.low_price is not None else None,
                    "成交量": float(p.volume) if p.volume is not None else None,
                    "成交额": float(p.amount) if p.amount is not None else None,
                }
            except Exception:
                return None

        rows = [r for r in (to_row(p) for p in prices) if r is not None]
        rows.sort(key=lambda x: x["日期"]) 
        return rows
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票数据失败: {str(e)}")


@app.post("/api/stock/analyze")
async def analyze_stock_api(request: AnalyzeStockRequest):
    """分析股票数据"""
    try:
        analysis_text, data_table, chart = analyze_stock(
            request.stock_code,
            request.interval
        )
        
        # 处理错误情况
        if isinstance(analysis_text, str) and (
            analysis_text.startswith("请输入") or 
            analysis_text.startswith("获取") or 
            analysis_text.startswith("分析失败")
        ):
            raise HTTPException(status_code=400, detail=analysis_text)
        
        # 转换数据表格
        data_table_list = []
        if data_table is not None and not data_table.empty:
            data_table_list = [
                StockDataResponse(**row) 
                for row in data_table.to_dict('records')
            ]
        
        # 转换图表数据
        chart_data = None
        if chart is not None:
            # 从 Plotly 图表对象中提取数据
            try:
                chart_dict = chart.to_dict()
                if 'data' in chart_dict:
                    dates = []
                    stocks_data = []
                    
                    for trace in chart_dict['data']:
                        if 'x' in trace and 'y' in trace:
                            code = trace.get('name', 'Unknown')
                            # 处理 x 轴数据（日期）
                            x_data = trace['x']
                            if isinstance(x_data, list) and len(x_data) > 0:
                                if not dates:
                                    # 转换日期格式
                                    dates = [str(d) for d in x_data]
                            
                            # 处理 y 轴数据（涨跌幅）
                            y_data = trace['y']
                            if isinstance(y_data, list):
                                returns = [float(v) if v is not None else 0.0 for v in y_data]
                                stocks_data.append({
                                    'code': code,
                                    'returns': returns
                                })
                    
                    if dates and stocks_data:
                        chart_data = StockChartData(
                            dates=dates,
                            stocks=stocks_data
                        )
            except Exception as e:
                print(f"转换图表数据失败: {e}")
                import traceback
                traceback.print_exc()
        
        return StockAnalysisResponse(
            analysis_text=analysis_text,
            data_table=data_table_list,
            chart_data=chart_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/api/chat")
async def chat_api(request: ChatRequest):
    """与 LangGraph Agent 对话"""
    try:
        # 转换历史记录格式
        chat_history = []
        if request.history:
            for msg in request.history:
                if isinstance(msg, dict):
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    if role == 'user':
                        chat_history.append((content, ''))
                    elif role == 'assistant':
                        if chat_history:
                            chat_history[-1] = (chat_history[-1][0], content)
        
        # 调用聊天函数
        updated_history, _ = chat_with_agent(request.message, chat_history)
        
        # 获取最后一条助手回复
        if updated_history and len(updated_history) > 0:
            last_message = updated_history[-1]
            if len(last_message) >= 2:
                bot_reply = last_message[1]
                return ChatResponse(message=bot_reply)
        
        return ChatResponse(message="抱歉，没有收到回复")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话出错: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

