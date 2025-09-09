from typing import Literal, Optional, Union
import pandas as pd
from .config import config


def process_dataframe(
    df: pd.DataFrame,
    format: Optional[Literal['markdown', 'json', 'dict']] = 'markdown',
    max_rows: Optional[int] = None,
) -> Union[str, pd.DataFrame]:
    if df is None or df.empty:
        return "数据为空" if format is not None else pd.DataFrame()

    if max_rows is None:
        max_rows = config.default_max_rows

    total_rows, total_cols = df.shape

    if total_rows > max_rows:
        df_limited = df.head(max_rows)
    else:
        df_limited = df

    if format is None:
        return df_limited

    if format == 'markdown':
        result = df_limited.to_markdown()
    elif format == 'json':
        result = df_limited.to_dict(orient='records')
    elif format == 'dict':
        result = df_limited.to_dict(orient='records')
    else:
        raise ValueError(f"不支持的格式: {format}，请使用 'markdown', 'json', 'dict' 或 None")
    return result


def _calculate_price_hist(df: pd.DataFrame, sort_by: str = '时间'):
    df = df.sort_values(sort_by).reset_index(drop=True)

    if len(df) > 0:
        df['开盘'] = df['收盘'].shift(1)
        df.loc[0, '开盘'] = df.loc[0, '收盘']

    df['涨跌幅'] = round((df['收盘'] - df['开盘']) / df['开盘'] * 100, 2)
    df['涨跌额'] = round(df['收盘'] - df['开盘'], 2)
    df['振幅'] = round((df['最高'] - df['最低']) / df['开盘'] * 100, 2)
    return df


