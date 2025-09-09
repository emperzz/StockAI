from datetime import datetime, timedelta
import pandas as pd
from typing import Optional
from .config import config


def normalize_dates(start_date: Optional[str], end_date: Optional[str]) -> tuple[str, str]:
    if not end_date:
        end_date = datetime.now().strftime('%Y%m%d')
    else:
        end_date = pd.to_datetime(end_date).strftime('%Y%m%d')

    if not start_date:
        start_date = (datetime.strptime(end_date, '%Y%m%d') - timedelta(days=config.default_lookback_days)).strftime('%Y%m%d')
    else:
        start_date = pd.to_datetime(start_date).strftime('%Y%m%d')

    if start_date > end_date:
        raise ValueError(f"开始日期不能大于结束日期: {start_date} > {end_date}")

    return start_date, end_date


def validate_stock_code(stock_code: str) -> bool:
    return bool(stock_code) and len(stock_code) == 6 and stock_code.isdigit()


def _format_time(time_str):
    if pd.isna(time_str) or time_str == '':
        return '未知'
    time_str = str(time_str)
    if len(time_str) >= 6:
        return f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
    return str(time_str)


