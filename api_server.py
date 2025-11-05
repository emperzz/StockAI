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
import pandas as pd

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入 gradio_app 中的函数
from stockai.frontend.gradio_app import (
    get_stock_info,
    get_stock_data,
    get_multi_stock_data,
    create_return_line_chart,
    analyze_stock,
    chat_with_agent,
)

app = FastAPI(title="StockAI API", version="1.0.0")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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


@app.get("/api/stock/info/{stock_code}")
async def get_stock_info_api(stock_code: str):
    """获取股票基本信息"""
    try:
        result = get_stock_info(stock_code)
        # 将 DataFrame 转换为字典列表
        if hasattr(result, 'to_dict'):
            return result.to_dict('records')
        return {"info": str(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票信息失败: {str(e)}")


@app.get("/api/stock/data/{stock_code}")
async def get_stock_data_api(stock_code: str, interval: str = "1d", days: int = 30):
    """获取股票历史数据"""
    try:
        result = get_stock_data(stock_code, interval=interval, days=days)
        if isinstance(result, str):
            raise HTTPException(status_code=500, detail=result)
        # 将 DataFrame 转换为字典列表
        return result.to_dict('records')
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

