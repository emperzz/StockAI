from typing import Literal, Optional, Union
from datetime import datetime
import akshare as ak
from akshare.stock_a.stock_zh_a_spot import process_data
import pandas as pd

from .client import safe_akshare_call, retry_decorator
from .cache import cache
from cachetools import cached
from .processors import process_dataframe, _calculate_price_hist
from .utils import normalize_dates, validate_stock_code, _format_time


@cached(cache)
@retry_decorator
def get_trading_calendar(format: Optional[Literal['markdown', 'json', 'dict']] = 'markdown') -> Union[str, pd.DataFrame]:
    """
    获取中国 A 股交易日历。

    参数:
    - format: 'markdown' | 'json' | 'dict' | None；None 返回 DataFrame。

    返回:
    - 依据 format 返回 Markdown 字符串、List[Dict] 或 DataFrame。
    """
    try:
        df = safe_akshare_call(ak.tool_trade_date_hist_sina)
        if len(df.columns) >= 2:
            df.columns = ['date', 'is_open'] + list(df.columns[2:])
        return process_dataframe(df, format=format, max_rows=100)
    except Exception as e:
        return f"获取交易日历失败: {e}"

def is_trading_date(date: str):
    """
    判断指定日期是否为交易日。

    参数:
    - date: 'YYYY-MM-DD' 字符串。

    返回:
    - bool：是否为交易日。
    """
    df = ak.tool_trade_date_hist_sina()
    return date in df.trade_date.astype(str).values

def get_current_time():
    """
    返回当前时间信息（字符串），包含时间、星期与是否为交易日。

    返回:
    - str: 如 "当前时间: 2024-06-01 10:00:00, 星期：星期一, 是否是交易日：True"。
    """
    week_list = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
    now = datetime.now()
    return f"""当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}, 
            星期：{week_list[now.weekday()]}, 
            是否是交易日：{is_trading_date(now.strftime('%Y-%m-%d'))}"""


@cached(cache)
@retry_decorator
def get_limitup_stocks_by_date(date: str, format: Optional[Literal['markdown', 'json', 'dict']] = 'markdown') -> Union[str, pd.DataFrame]:
    """
    获取指定日期的涨停股票列表。

    参数:
    - date: 'YYYYMMDD'。
    - format: 'markdown'|'json'|'dict'|None；None 返回 DataFrame。

    返回:
    - 涨停股票列表，时间列已格式化。
    """
    try:
        df = safe_akshare_call(ak.stock_zt_pool_em, date=date)
        if df is not None and not df.empty:
            df['首次封板时间'] = df['首次封板时间'].apply(_format_time)
            df['最后封板时间'] = df['最后封板时间'].apply(_format_time)
            return process_dataframe(df, format=format, max_rows=200)
        else:
            return "没有找到涨停股票数据" if format is not None else pd.DataFrame()
    except Exception as e:
        return f"获取涨停股票数据失败: {e}"


@cached(cache)
@retry_decorator
def get_index_realtime_data(format: Optional[Literal['markdown', 'json', 'dict']] = 'markdown') -> Union[str, pd.DataFrame]:
    """
    获取沪深重要指数实时行情。

    参数:
    - format: 'markdown'|'json'|'dict'|None；None 返回 DataFrame。

    返回:
    - 指数实时数据。
    """
    try:
        df = safe_akshare_call(ak.stock_zh_index_spot_em, symbol='沪深重要指数')
        return process_dataframe(df, format=format, max_rows=50)
    except Exception as e:
        return f"获取指数实时价格失败: {e}"


@cached(cache)
@retry_decorator
def get_index_kline(symbol: str,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None,
                    period: Literal['1', '5', '15', '30', '60', 'daily', 'weekly'] = 'daily',
                    format: Optional[Literal['markdown', 'json', 'dict']] = 'dict') -> Union[str, pd.DataFrame]:
    """
    获取指数历史行情（分时/日/周）。

    参数:
    - symbol: 指数代码（如 '000001'）。
    - start_date/end_date: 'YYYYMMDD'，可空。
    - period: '1'|'5'|'15'|'30'|'60'|'daily'|'weekly'。
    - format: 'markdown'|'json'|'dict'|None；None 返回 DataFrame。

    返回:
    - 历史行情数据。
    """
    try:
        start_date, end_date = normalize_dates(start_date, end_date)

        if period in ['daily', 'weekly']:
            df = safe_akshare_call(
                ak.index_zh_a_hist,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                period=period
            )
            keep = ['日期', '开盘', '收盘', '最高', '最低', '涨跌幅', '涨跌额', '成交量', '成交额', '振幅', '换手率']
            df = df[[c for c in keep if c in df.columns]]
        else:
            df = safe_akshare_call(
                ak.index_zh_a_hist_min_em,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                period=period
            )
            if period == '1':
                base_cols = ['时间', '成交量', '成交额', '开盘', '收盘', '最高', '最低']
                df = _calculate_price_hist(df[[c for c in base_cols if c in df.columns]])
            else:
                keep = ['时间', '成交量', '成交额', '开盘', '收盘', '最高', '最低', '涨跌幅', '涨跌额', '振幅', '换手率']
                df = df[[c for c in keep if c in df.columns]]
            df.rename(columns={'时间': '日期'}, inplace=True)

        return process_dataframe(df, format=format, max_rows=1000)
    except Exception as e:
        return f"获取指数价格历史数据失败: {e}"


@cached(cache)
@retry_decorator
def get_concept_kline(concept_name: str,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      period: Literal['1', '5', '15', '30', '60', 'daily', 'weekly'] = 'daily',
                      format: Optional[Literal['markdown', 'json', 'dict']] = 'dict') -> Union[str, pd.DataFrame]:
    """
    获取板块（概念）历史行情（分时/日/周）。

    参数:
    - concept_name: 板块名称。
    - start_date/end_date: 'YYYYMMDD'，可空。
    - period: '1'|'5'|'15'|'30'|'60'|'daily'|'weekly'。
    - format: 'markdown'|'json'|'dict'|None；None 返回 DataFrame。

    返回:
    - 历史行情数据。
    """
    try:
        start_date, end_date = normalize_dates(start_date, end_date)

        if period in ['daily', 'weekly']:
            df = safe_akshare_call(
                ak.stock_board_concept_hist_em,
                symbol=concept_name,
                start_date=start_date,
                end_date=end_date,
                period=period
            )
            keep = ['日期', '开盘', '收盘', '最高', '最低', '涨跌幅', '涨跌额', '成交量', '成交额', '振幅', '换手率']
            df = df[[c for c in keep if c in df.columns]]
        else:
            df = safe_akshare_call(
                ak.stock_board_concept_hist_min_em,
                symbol=concept_name,
                period=period
            )
            if period == '1':
                base_cols = ['日期时间', '成交量', '成交额', '开盘', '收盘', '最高', '最低']
                df = _calculate_price_hist(df[[c for c in base_cols if c in df.columns]], sort_by='日期时间')
            else:
                keep = ['日期时间', '成交量', '成交额', '开盘', '收盘', '最高', '最低', '涨跌幅', '涨跌额', '振幅', '换手率']
                df = df[[c for c in keep if c in df.columns]]
                df.set_index(pd.to_datetime(df['日期时间']), inplace=True)
                df = df[start_date:end_date]
                df.reset_index(drop=True, inplace=True)
            df.rename(columns={'日期时间': '日期'}, inplace=True)

        return process_dataframe(df, format=format, max_rows=300)
    except Exception as e:
        return f"获取板块价格历史数据失败: {e}"


@cached(cache)
@retry_decorator
def get_stock_kline(stock_code: str,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None,
                    period: Literal['1', '5', '15', '30', '60', 'daily', 'weekly'] = 'daily',
                    format: Optional[Literal['markdown', 'json', 'dict']] = 'dict') -> Union[str, pd.DataFrame]:
    """
    获取个股历史行情（分时/日/周）。

    参数:
    - stock_code: 6 位股票代码。
    - start_date/end_date: 'YYYYMMDD'，可空。
    - period: '1'|'5'|'15'|'30'|'60'|'daily'|'weekly'。
    - format: 'markdown'|'json'|'dict'|None；None 返回 DataFrame。

    返回:
    - 历史行情数据。
    """
    try:
        if not validate_stock_code(stock_code):
            return "股票代码格式错误，应为6位数字"

        start_date, end_date = normalize_dates(start_date, end_date)

        if period in ['daily', 'weekly']:
            df = safe_akshare_call(
                ak.stock_zh_a_hist,
                symbol=stock_code,
                start_date=start_date,
                end_date=end_date,
                period=period
            )
            keep = ['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '涨跌幅', '涨跌额', '振幅', '换手率']
            df = df[[c for c in keep if c in df.columns]]
            if '日期' in df.columns:
                df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
        else:
            df = safe_akshare_call(
                ak.stock_zh_a_hist_min_em,
                symbol=stock_code,
                start_date=start_date,
                end_date=end_date,
                period=period,
                adjust="qfq"
            )
            if period == '1':
                base_cols = ['时间', '成交量', '成交额', '开盘', '收盘', '最高', '最低']
                df = _calculate_price_hist(df[[c for c in base_cols if c in df.columns]], sort_by='时间')
            else:
                keep = ['时间', '成交量', '成交额', '开盘', '收盘', '最高', '最低', '涨跌幅', '涨跌额', '振幅', '换手率']
                df = df[[c for c in keep if c in df.columns]]
            df.rename(columns={'时间': '日期'}, inplace=True)

        return process_dataframe(df, format=format, max_rows=1000)
    except Exception as e:
        return f"获取股票价格历史数据失败: {e}"


@cached(cache)
@retry_decorator
def get_stock_realtime_data(format: Optional[Literal['markdown', 'json', 'dict']] = 'dict',
                            sort_by: Optional[Literal['涨跌幅', '换手率', '成交量', '成交额', '总市值', '振幅', '量比']] = None,
                            desc: bool = True,
                            top_n: int = 100) -> Union[str, pd.DataFrame]:
    """
    获取沪深京 A 股实时行情列表。

    参数:
    - format: 'markdown'|'json'|'dict'|None；None 返回 DataFrame。
    - sort_by: 排序字段，可空。
    - desc: 是否降序。
    - top_n: 返回前 N 行。

    返回:
    - 实时行情列表。
    """
    try:
        df = safe_akshare_call(ak.stock_zh_a_spot_em)
        if sort_by and sort_by in df.columns:
            df = df.sort_values(by=sort_by, ascending=not desc)
        drop_cols = [c for c in ['序号','涨速','5分钟涨跌'] if c in df.columns]
        df.drop(columns=drop_cols, inplace=True, errors='ignore')
        return process_dataframe(df.head(top_n), format=format)
    except Exception as e:
        return f"获取股票列表失败: {e}"


@cached(cache)
@retry_decorator
def get_concept_realtime_data(top_n: int = 20, format: Optional[Literal['markdown', 'json', 'dict']] = 'dict', exclude: Optional[str] = None) -> Union[str, pd.DataFrame]:
    """
    获取概念板块实时行情列表。

    参数:
    - top_n: 返回前 N 个板块。
    - format: 'markdown'|'json'|'dict'|None；None 返回 DataFrame。
    - exclude: 过滤名称包含该子串的板块。

    返回:
    - 板块实时列表。
    """
    try:
        df = safe_akshare_call(ak.stock_board_concept_name_em)
        if exclude:
            df = df[df.板块名称.str.contains(exclude) == False]
        keep = ['板块名称', '板块代码', '最新价', '涨跌额', '涨跌幅', '换手率', '上涨家数', '下跌家数']
        df = df[[c for c in keep if c in df.columns]].head(top_n)
        return process_dataframe(df, format=format)
    except Exception as e:
        return f"获取板块列表失败: {e}"
    
@cached(cache)
@retry_decorator
def get_concept_stocks_realtime_data(concept_code: str, top_n: int = 100, format: Optional[Literal['markdown', 'json', 'dict']] = 'dict'):
    """
    获取概念板块实时行情列表。

    参数:
    - concept_code: 板块代码
    - top_n: 返回前 N 个股票。
    - format: 'markdown'|'json'|'dict'|None；None 返回 DataFrame。

    返回:
    - 板块内的实时股票列表。
    """
    try:
        df = safe_akshare_call(ak.stock_board_industry_cons_em, symbol=concept_code)
        drop_cols = [c for c in ['序号','市盈率-动'] if c in df.columns]
        df.drop(columns=drop_cols, inplace=True, errors='ignore')
        return process_dataframe(df, format = format, max_rows = top_n)
    except Exception as e:
        return f"获取板块详情失败: {e}"


@cached(cache)
@retry_decorator
def get_index_list(format: Optional[Literal['markdown', 'json', 'dict']] = 'dict') -> Union[str, pd.DataFrame]:
    """
    获取重要指数清单（两列：名称、代码）。

    参数:
    - format: 'markdown'|'json'|'dict'|None；None 返回 DataFrame。

    返回:
    - 两列结构：['名称','代码']。
    """
    try:
        df = get_index_realtime_data(format=None)
        if isinstance(df, pd.DataFrame) and not df.empty:
            if '名称' in df.columns and '代码' in df.columns:
                df = df[['名称', '代码']].copy()
            else:
                name_col = '名称' if '名称' in df.columns else ('name' if 'name' in df.columns else None)
                code_col = '代码' if '代码' in df.columns else ('symbol' if 'symbol' in df.columns else None)
                if name_col and code_col:
                    df = df[[name_col, code_col]].copy()
                    df.rename(columns={name_col: '名称', code_col: '代码'}, inplace=True)
                else:
                    return "数据格式不包含名称/代码列" if format is not None else pd.DataFrame()
            return process_dataframe(df, format=format, max_rows=1000)
        return "数据为空" if format is not None else pd.DataFrame()
    except Exception as e:
        return f"获取指数清单失败: {e}"


@cached(cache)
@retry_decorator
def get_stock_list(format: Optional[Literal['markdown', 'json', 'dict']] = 'dict') -> Union[str, pd.DataFrame]:
    """
    获取全市场股票清单（两列：名称、代码）。

    参数:
    - format: 'markdown'|'json'|'dict'|None；None 返回 DataFrame。

    返回:
    - 两列结构：['名称','代码']。
    """
    try:
        df = get_stock_realtime_data(format=None, top_n=100000)
        if isinstance(df, pd.DataFrame) and not df.empty:
            if '名称' in df.columns and '代码' in df.columns:
                df = df[['名称', '代码']].copy()
            else:
                name_col = '名称' if '名称' in df.columns else ('name' if 'name' in df.columns else None)
                code_col = '代码' if '代码' in df.columns else ('symbol' if 'symbol' in df.columns else None)
                if name_col and code_col:
                    df = df[[name_col, code_col]].copy()
                    df.rename(columns={name_col: '名称', code_col: '代码'}, inplace=True)
                else:
                    return "数据格式不包含名称/代码列" if format is not None else pd.DataFrame()
            return process_dataframe(df, format=format, max_rows=6000)
        return "数据为空" if format is not None else pd.DataFrame()
    except Exception as e:
        return f"获取股票清单失败: {e}"


@cached(cache)
@retry_decorator
def get_concept_list(format: Optional[Literal['markdown', 'json', 'dict']] = 'dict') -> Union[str, pd.DataFrame]:
    """
    获取概念板块清单（两列：名称、代码）。

    参数:
    - format: 'markdown'|'json'|'dict'|None；None 返回 DataFrame。

    返回:
    - 两列结构：['名称','代码']。
    """
    try:
        df = get_concept_realtime_data(format=None, top_n=100000)
        if isinstance(df, pd.DataFrame) and not df.empty:
            if '板块名称' in df.columns and '板块代码' in df.columns:
                df = df[['板块名称', '板块代码']].copy()
                df.rename(columns={'板块名称': '名称', '板块代码': '代码'}, inplace=True)
            else:
                name_col = '名称' if '名称' in df.columns else ('板块名称' if '板块名称' in df.columns else None)
                code_col = '代码' if '代码' in df.columns else ('板块代码' if '板块代码' in df.columns else None)
                if name_col and code_col:
                    df = df[[name_col, code_col]].copy()
                    df.rename(columns={name_col: '名称', code_col: '代码'}, inplace=True)
                else:
                    return "数据格式不包含名称/代码列" if format is not None else pd.DataFrame()
            return process_dataframe(df, format=format, max_rows=1000)
        return "数据为空" if format is not None else pd.DataFrame()
    except Exception as e:
        return f"获取板块清单失败: {e}"


@cached(cache)
@retry_decorator
def get_concept_stocks_list(concept_code: str, format: Optional[Literal['markdown', 'json', 'dict']] = 'dict'):
    """
    获取概念板块实时行情列表。

    参数:
    - concept_code: 板块代码
    - top_n: 返回前 N 个股票。
    - format: 'markdown'|'json'|'dict'|None；None 返回 DataFrame。

    返回:
    - 板块内的实时股票列表。
    """
    try:
        df = get_concept_stocks_realtime_data(concept_code = concept_code, format=None, top_n=100000)
        if isinstance(df, pd.DataFrame) and not df.empty:
            if '名称' in df.columns and '代码' in df.columns:
                df = df[['名称', '代码']].copy()
            else:
                name_col = '名称' if '名称' in df.columns else ('name' if 'name' in df.columns else None)
                code_col = '代码' if '代码' in df.columns else ('symbol' if 'symbol' in df.columns else None)
                if name_col and code_col:
                    df = df[[name_col, code_col]].copy()
                    df.rename(columns={name_col: '名称', code_col: '代码'}, inplace=True)
                else:
                    return "数据格式不包含名称/代码列" if format is not None else pd.DataFrame()
            return process_dataframe(df, format=format, max_rows=1000)
        return "数据为空" if format is not None else pd.DataFrame()
    except Exception as e:
        return f"获取板块清单失败: {e}"

@cached(cache)
@retry_decorator
def get_code_or_name(entity_type: Literal['stock', 'index', 'concept'],
                     code: Optional[str] = None,
                     name: Optional[str] = None) -> str:
    """
    名称/代码互查工具（精确匹配）。

    约束:
    - code 与 name 必须有且仅有一个有值。

    参数:
    - entity_type: 'stock'|'index'|'concept'。
    - code: 代码（若提供则返回名称）。
    - name: 名称（若提供则返回代码）。

    返回:
    - str: 互查结果；未找到或参数错误时返回提示。
    """
    try:
        has_code = bool(code)
        has_name = bool(name)
        if has_code == has_name:
            return "参数错误：code 和 name 必须有且仅有一个有值"

        if entity_type == 'stock':
            df = get_stock_list(format=None)
        elif entity_type == 'index':
            df = get_index_list(format=None)
        elif entity_type == 'concept':
            df = get_concept_list(format=None)
        else:
            return f"不支持的类型: {entity_type}"

        if not isinstance(df, pd.DataFrame) or df.empty or '名称' not in df.columns or '代码' not in df.columns:
            return "数据为空或缺少必要列"

        if has_code:
            code_str = str(code).strip()
            matched = df[df['代码'].astype(str).str.strip() == code_str]
            if matched.empty:
                return "未找到匹配项"
            return str(matched.iloc[0]['名称'])
        else:
            name_str = str(name).strip()
            matched = df[df['名称'].astype(str).str.strip() == name_str]
            if matched.empty:
                return "未找到匹配项"
            return str(matched.iloc[0]['代码'])
    except Exception as e:
        return f"解析失败: {e}"


    
    
@cached(cache)
@retry_decorator
def get_concept_detail(concept_code: str, format: Optional[Literal['markdown', 'json', 'dict']] = 'dict') -> Union[str, dict]:
    """
    获取指定板块的成分股明细，并标注涨停情况与统计。

    参数:
    - concept_code: 板块代码（如 'BK1128'）。
    - format: 'markdown'|'json'|'dict'|None；None 返回 DataFrame。

    返回:
    - dict 或 DataFrame：包含日期、板块代码、成分股列表、涨停统计。
    """
    try:
        df = safe_akshare_call(ak.stock_board_industry_cons_em, symbol=concept_code)
        today = datetime.now().strftime('%Y%m%d')
        limitup_df = safe_akshare_call(ak.stock_zt_pool_em, date=today)

        result = {
            'date': today,
            '板块代码': concept_code,
            '板块内股票数量': len(df) if df is not None else 0,
            '涨停统计': {
                '涨停总数': 0,
                '30%涨停股票数量': 0,
                '20%涨停股票数量': 0,
                '10%涨停股票数量': 0
            }
        }

        limitup_cnt_30 = 0
        limitup_cnt_20 = 0
        limitup_cnt_10 = 0

        if df is not None and not df.empty and limitup_df is not None and not limitup_df.empty:
            def add_limitup_info(row):
                nonlocal limitup_cnt_30, limitup_cnt_20, limitup_cnt_10
                stock_code = row['代码']
                limitup_stock = limitup_df[limitup_df['代码'] == stock_code]
                if not limitup_stock.empty:
                    try:
                        change_pct = float(row['涨跌幅'])
                        if change_pct > 25:
                            limitup_cnt_30 += 1
                        elif change_pct > 15:
                            limitup_cnt_20 += 1
                        elif change_pct > 5:
                            limitup_cnt_10 += 1
                    except (ValueError, TypeError):
                        pass

                    limitup_info = limitup_stock.iloc[0]
                    limitup_situation = {
                        '封板资金': int(limitup_info.get('封板资金', '0')),
                        '首次封板时间': _format_time(limitup_info.get('首次封板时间', '')),
                        '最后封板时间': _format_time(limitup_info.get('最后封板时间', '')),
                        '炸板次数': int(limitup_info.get('炸板次数', '0')),
                        '涨停统计': limitup_info.get('涨停统计', '未知'),
                        '连板数': int(limitup_info.get('连板数', '0'))
                    }
                    row['涨停情况'] = limitup_situation
                    row['是否涨停'] = '是'
                else:
                    row['涨停情况'] = None
                    row['是否涨停'] = '否'
                return row

            df = df.apply(add_limitup_info, axis=1)
            base_columns = ['代码', '名称', '是否涨停', '涨停情况']
            other_columns = [col for col in df.columns if col not in base_columns]
            df = df[base_columns + other_columns]
            result['涨停统计'] = {
                '涨停总数': limitup_cnt_30 + limitup_cnt_20 + limitup_cnt_10,
                '30%涨停股票数量': limitup_cnt_30,
                '20%涨停股票数量': limitup_cnt_20,
                '10%涨停股票数量': limitup_cnt_10
            }
            result['板块明细'] = process_dataframe(df, format=format, max_rows=300)
            return result
        else:
            if df is None or df.empty:
                return "未找到板块成分股数据"
            elif limitup_df is None or limitup_df.empty:
                df['是否涨停'] = '未知'
                df['涨停情况'] = None
                result['板块明细'] = process_dataframe(df, format=format, max_rows=300)
                return result
            else:
                return "数据获取异常"
    except Exception as e:
        return f"获取板块详情失败: {e}"


@cached(cache)
@retry_decorator
def get_stock_basic_info(stock_code: str, format: Optional[Literal['markdown', 'json', 'dict']] = 'dict') -> Union[str, dict]:
    """
    获取个股基本信息与关键指标。

    参数:
    - stock_code: 6 位股票代码。
    - format: 'markdown'|'json'|'dict'|None；None 返回 DataFrame。

    返回:
    - 基本信息（含总股本、流通股、本/流通市值、行业等）。
    """
    try:
        if not validate_stock_code(stock_code):
            return "股票代码格式错误，应为6位数字"

        df = safe_akshare_call(ak.stock_profile_cninfo, stock_code)
        df1 = safe_akshare_call(ak.stock_individual_info_em, symbol=stock_code).set_index('item').T.to_dict(orient='records')

        df['总股本'] = df1[0].get('总股本')
        df['流通股'] = df1[0].get('流通股')
        df['流通市值'] = df1[0].get('流通市值')
        df['总市值'] = df1[0].get('总市值')
        df['行业'] = df1[0].get('行业')

        res = process_dataframe(df, format=format)
        return res[0] if isinstance(res, list) and len(res) > 0 else res
    except Exception as e:
        return f"获取股票基本信息失败: {e}"


