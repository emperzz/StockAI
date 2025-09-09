# AKShare数据获取客户端
# 封装AKShare API调用，获取中国股市数据

from math import e
import akshare as ak
from typing import Literal, Optional, Union
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass
from cachetools import TTLCache, cached
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AkshareConfig:
    """AKShare配置管理"""
    # 缓存配置
    cache_maxsize: int = 128
    cache_ttl: int = 600  # 10分钟
    
    # 重试配置
    max_retries: int = 3
    retry_wait_min: float = 1.0
    retry_wait_max: float = 10.0
    
    # 数据配置
    default_max_rows: int = 120
    default_lookback_days: int = 365
    
    # 涨停阈值
    limitup_threshold_30: float = 25.0
    limitup_threshold_20: float = 15.0
    limitup_threshold_10: float = 5.0

# 全局配置实例
config = AkshareConfig()

# 创建缓存实例
cache = TTLCache(maxsize=config.cache_maxsize, ttl=config.cache_ttl)

# 重试装饰器
retry_decorator = retry(
    stop=stop_after_attempt(config.max_retries),
    wait=wait_exponential(multiplier=1, min=config.retry_wait_min, max=config.retry_wait_max),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception))
)

# 工具函数
def normalize_dates(start_date: Optional[str], end_date: Optional[str]) -> tuple[str, str]:
    """统一处理日期参数"""
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
    """验证股票代码格式"""
    return stock_code and len(stock_code) == 6 and stock_code.isdigit()

def safe_akshare_call(api_func, *args, **kwargs):
    """安全的AKShare API调用"""
    try:
        logger.info(f"调用AKShare API: {api_func.__name__}")
        result = api_func(*args, **kwargs)
        logger.info(f"API调用成功: {api_func.__name__}")
        return result
    except Exception as e:
        logger.error(f"API调用失败: {api_func.__name__}, 错误: {e}")
        raise

def process_dataframe(df: pd.DataFrame, 
                     format: Optional[Literal['markdown', 'json', 'dict']] = 'markdown',
                     max_rows: Optional[int] = None) -> Union[str, pd.DataFrame]:
    """
    统一处理DataFrame的返回格式和数据量控制
    
    Args:
        df: 要处理的DataFrame
        format: 返回格式，可选 'markdown', 'json', 'dict', None。如果为None，返回原始DataFrame
        max_rows: 最大返回行数，超过则截取前max_rows行
    
    Returns:
        根据format参数返回相应格式的数据，如果format为None则返回DataFrame
    """
    if df is None or df.empty:
        return "数据为空" if format is not None else pd.DataFrame()
    
    # 使用配置中的默认值
    if max_rows is None:
        max_rows = config.default_max_rows
    
    # 获取原始数据信息
    total_rows, total_cols = df.shape
    
    # 数据量控制：如果数据量太大，只返回前max_rows行
    if total_rows > max_rows:
        df_limited = df.head(max_rows)
        data_info = f"数据量较大，显示前{max_rows}行（共{total_rows}行，{total_cols}列）"
    else:
        df_limited = df
        data_info = f"共{total_rows}行，{total_cols}列"
    
    # 如果format为None，直接返回DataFrame
    if format is None:
        return df_limited
    
    # 根据格式返回数据
    if format == 'markdown':
        result = df_limited.to_markdown()

    elif format == 'json':
        result = df_limited.to_dict(orient='records')
        # result = df_limited.to_json(orient='records', force_ascii=False, indent=2)
    #     if show_info:
    #         result = {
    #             "info": data_info,
    #             "data": df_limited.to_dict(orient='records')
    #         }
    #         return result
    
    elif format == 'dict':
        result = df_limited.to_dict(orient='records')

    else:
        raise ValueError(f"不支持的格式: {format}，请使用 'markdown', 'json', 'dict' 或 None")
    return result


@cached(cache)
@retry_decorator
def get_trading_calendar(format: Optional[Literal['markdown', 'json', 'dict']] = 'markdown') -> Union[str, pd.DataFrame]:
    """
    获取交易日历
    
    Args:
        format: 返回格式，可选 'markdown', 'json', 'dict', None。如果为None，返回原始DataFrame
    
    Returns:
        根据format参数返回相应格式的交易日历数据，如果format为None则返回DataFrame
    """
    try:
        df = safe_akshare_call(ak.tool_trade_date_hist_sina)
        # 检查DataFrame的列数，确保列名设置正确
        if len(df.columns) >= 2:
            df.columns = ['date', 'is_open'] + list(df.columns[2:])
        return process_dataframe(df, format=format, max_rows=100)
    except Exception as e:
        logger.error(f"获取交易日历失败: {e}")
        return f"获取交易日历失败: {e}"

def is_trading_date(date: str):
    """
    判断是否为交易日
    
    Args:
        date: 日期，格式为YYYY-MM-DD
    """
    df = ak.tool_trade_date_hist_sina()
    return date in df.trade_date.astype(str).values

def get_current_time():
    """
    获取当前时间
    
    Returns:
        str: 对当前时间的寿命，格式为YYYY-MM-DD HH:MM:SS，星期，是否是交易日
    """ 
    week_list = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
    now = datetime.now()
    return f"""当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}, 
            星期：{week_list[now.weekday()]}, 
            是否是交易日：{is_trading_date(now.strftime('%Y-%m-%d'))}"""


def _format_time(time_str):
    if pd.isna(time_str) or time_str == '':
        return '未知'
    time_str = str(time_str)
    if len(time_str) >= 6:
        return f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
    return str(time_str)

@cached(cache)
@retry_decorator
def get_limitup_stocks_by_date(date: str, format: Optional[Literal['markdown', 'json', 'dict']] = 'markdown') -> Union[str, pd.DataFrame]:
    """
    根据日期获取涨停股票数据
    
    Args:
        date: 日期，格式为YYYYMMDD
        format: 返回格式，可选 'markdown', 'json', 'dict', None。如果为None，返回原始DataFrame
    
    Returns:
        根据format参数返回相应格式的涨停股票数据，如果format为None则返回DataFrame
    """
    try:
        df = safe_akshare_call(ak.stock_zt_pool_em, date=date)
        if df is not None and not df.empty:
            df['首次封板时间'] = _format_time(df['首次封板时间'])
            df['最后封板时间'] = _format_time(df['最后封板时间'])
            
            # 使用统一的数据处理函数
            return process_dataframe(df, format=format, max_rows=200)
        else:
            return "没有找到涨停股票数据" if format is not None else pd.DataFrame()
    except Exception as e:
        logger.error(f"获取涨停股票数据失败: {e}")
        return f"获取涨停股票数据失败: {e}"

@cached(cache)
@retry_decorator
def get_all_index_price_realtime(format: Optional[Literal['markdown', 'json', 'dict']] = 'markdown') -> Union[str, pd.DataFrame]:
    """
    获取所有重要指数的实时价格
    
    Args:
        format: 返回格式，可选 'markdown', 'json', 'dict', None。如果为None，返回原始DataFrame
    
    Returns:
        根据format参数返回相应格式的指数数据，如果format为None则返回DataFrame
    """
    try:
        df = safe_akshare_call(ak.stock_zh_index_spot_em, symbol='沪深重要指数')
        return process_dataframe(df, format=format, max_rows=50)
    except Exception as e:
        logger.error(f"获取指数实时价格失败: {e}")
        return f"获取指数实时价格失败: {e}"


def _calculate_price_hist(df: pd.DataFrame, sort_by: str = '时间'):
    # 确保数据按时间排序（如果需要的话）
    df = df.sort_values(sort_by).reset_index(drop=True)
                
    # 应用新的开盘价逻辑
    if len(df) > 0:
        # 使用pandas的shift操作优化性能
        # 第一行的开盘价使用收盘价，后面每行的开盘价为上一行的收盘价
        df['开盘'] = df['收盘'].shift(1)  # 将收盘价向下移动一行
        df.loc[0, '开盘'] = df.loc[0, '收盘']  # 第一行开盘价使用收盘价
    
    df['涨跌幅'] = round((df['收盘'] - df['开盘']) / df['开盘'] * 100, 2)
    df['涨跌额'] = round(df['收盘'] - df['开盘'], 2)
    df['振幅'] = round((df['最高'] - df['最低']) / df['开盘'] * 100, 2) 
    # df['换手率'] = df['成交量'] / df['总股本']
    return df

@cached(cache)
@retry_decorator
def get_index_price_hist(symbol: str, 
                         start_date: Optional[str] = None, 
                         end_date: Optional[str] = None, 
                         period: Literal['1', '5', '15', '30', '60', 'daily', 'weekly'] = 'daily', 
                         format: Optional[Literal['markdown', 'json', 'dict']] = 'dict') -> Union[str, pd.DataFrame]:
    """
    获取指数价格历史数据
    
    Args:
        symbol: 指数代码
        start_date: 开始日期，格式为YYYYMMDD
        end_date: 结束日期，格式为YYYYMMDD
        period: 周期，可选 '1', '5', '15', '30', '60', 'daily', 'weekly'
        format: 返回格式，可选 'markdown', 'json', 'dict', None。如果为None，返回原始DataFrame
    
    Returns:
        根据format参数返回相应格式的指数价格历史数据，如果format为None则返回DataFrame
    """
    try:
        # 日期处理
        start_date, end_date = normalize_dates(start_date, end_date)
        
        if period in ['daily', 'weekly']:
            df = safe_akshare_call(
                ak.index_zh_a_hist,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                period=period
            )
            df = df[['日期', '开盘', '收盘', '最高', '最低', '涨跌幅', '涨跌额', '成交量', '成交额', '振幅', '换手率']]
        else:
            df = safe_akshare_call(
                ak.index_zh_a_hist_min_em,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                period=period
            )
            if period == '1':
                df = _calculate_price_hist(df[['时间', '成交量', '成交额', '开盘', '收盘', '最高', '最低']])
            else:
                df = df[['时间', '成交量', '成交额', '开盘', '收盘', '最高', '最低', '涨跌幅', '涨跌额', '振幅', '换手率']]
            df.rename(columns={'时间': '日期'}, inplace=True)
        
        return process_dataframe(df, format=format, max_rows=1000)
        
    except Exception as e:
        logger.error(f"获取指数价格历史数据失败: {e}")
        return f"获取指数价格历史数据失败: {e}"


@cached(cache)
@retry_decorator
def get_concept_price_hist(concept_name: str, 
                           start_date: Optional[str] = None, 
                           end_date: Optional[str] = None, 
                           period: Literal['1', '5', '15', '30', '60', 'daily', 'weekly'] = 'daily',
                           format: Optional[Literal['markdown', 'json', 'dict']] = 'dict') -> Union[str, pd.DataFrame]:
    """
    获取板块价格历史数据
    
    Args:
        concept_name: 板块名称
        start_date: 开始日期，格式为YYYYMMDD, 如果为空，则设置为end_date - 365days
        end_date: 结束日期，格式为YYYYMMDD, 如果为空，则设置为当前日期
        period: 周期，可选 '1', '5', '15', '30', '60', 'daily', 'weekly'
        format: 返回格式，可选 'markdown', 'json', 'dict', None。如果为None，返回原始DataFrame
    
    Returns:
        根据format参数返回相应格式的板块价格历史数据，如果format为None则返回DataFrame
    """
    try:
        # 日期处理
        start_date, end_date = normalize_dates(start_date, end_date)
        
        if period in ['daily', 'weekly']:
            df = safe_akshare_call(
                ak.stock_board_concept_hist_em,
                symbol=concept_name,
                start_date=start_date,
                end_date=end_date,
                period=period
            )
            df = df[['日期', '开盘', '收盘', '最高', '最低', '涨跌幅', '涨跌额', '成交量', '成交额', '振幅', '换手率']]
        else:
            df = safe_akshare_call(
                ak.stock_board_concept_hist_min_em,
                symbol=concept_name,
                period=period
            )
            if period == '1':
                df = _calculate_price_hist(df[['日期时间', '成交量', '成交额', '开盘', '收盘', '最高', '最低']], sort_by='日期时间')
            else:
                df = df[['日期时间', '成交量', '成交额', '开盘', '收盘', '最高', '最低', '涨跌幅', '涨跌额', '振幅', '换手率']]
                df.set_index(pd.to_datetime(df['日期时间']), inplace=True)
                df = df[start_date:end_date]
                df.reset_index(drop=True, inplace=True)
            df.rename(columns={'日期时间': '日期'}, inplace=True)
        
        return process_dataframe(df, format=format, max_rows=300)
        
    except Exception as e:
        logger.error(f"获取板块价格历史数据失败: {e}")
        return f"获取板块价格历史数据失败: {e}"

@cached(cache)
@retry_decorator
def get_stock_price_hist(stock_code: str, 
                         start_date: Optional[str] = None, 
                         end_date: Optional[str] = None, 
                         period : Literal['1', '5', '15', '30', '60', 'daily', 'weekly'] = 'daily',
                        format: Optional[Literal['markdown', 'json', 'dict']] = 'dict') -> Union[str, pd.DataFrame]:
    """获取股票价格历史数据

    Args:
        stock_code: 股票代码
        start_date: 开始日期，格式为YYYYMMDD, 如果为空，则设置为end_date - 365days
        end_date: 结束日期，格式为YYYYMMDD, 如果为空，则设置为当前日期
        period: 周期，可选 '1', '5', '15', '30', '60', 'daily', 'weekly'
        format: 返回格式，可选 'markdown', 'json', 'dict', None。如果为None，返回原始DataFrame

    Returns:
        根据format参数返回相应格式的股票价格历史数据，如果format为None则返回DataFrame
    """
    try:
        # 参数验证
        if not validate_stock_code(stock_code):
            return "股票代码格式错误，应为6位数字"
        
        # 日期处理
        start_date, end_date = normalize_dates(start_date, end_date)
        
        # 根据周期选择API
        if period in ['daily', 'weekly']:
            df = safe_akshare_call(
                ak.stock_zh_a_hist,
                symbol=stock_code,
                start_date=start_date,
                end_date=end_date,
                period=period
            )
            df = df[['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '涨跌幅', '涨跌额', '振幅', '换手率']]
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
                df = _calculate_price_hist(df[['时间', '成交量', '成交额', '开盘', '收盘', '最高', '最低']], sort_by='时间')
            else:
                df = df[['时间', '成交量', '成交额', '开盘', '收盘', '最高', '最低', '涨跌幅', '涨跌额', '振幅', '换手率']]
            df.rename(columns={'时间': '日期'}, inplace=True)
        
        return process_dataframe(df, format=format, max_rows=1000)
        
    except Exception as e:
        logger.error(f"获取股票价格历史数据失败: {e}")
        return f"获取股票价格历史数据失败: {e}"
        
    
@cached(cache)
@retry_decorator
def get_all_stock_list(format: Optional[Literal['markdown', 'json', 'dict']] = 'dict',
                       sort_by: Optional[Literal['涨跌幅', '换手率', '成交量', '成交额', '总市值', '振幅', '量比']] = None,
                       desc: bool = True,
                       top_n: int = 100) -> Union[str, pd.DataFrame]:
    """
    获取所有沪深京A股股票的实时行情数据
    
    Args:
        format: 返回格式，可选 'markdown', 'json', 'dict', None。如果为None，返回原始DataFrame
        sort_by: 排序字段，可选 '涨跌幅', '换手率', '成交量', '成交额', '总市值', '振幅', '量比'
        desc: 是否降序，默认 True
        top_n: 返回的行数，默认 100
    
    Returns:
        根据format参数返回相应格式的股票列表数据，如果format为None则返回DataFrame
    """
    try:
        df = safe_akshare_call(ak.stock_zh_a_spot_em)
        if sort_by:
            df = df.sort_values(by=sort_by, ascending=not desc)
        df.drop(columns=['序号','涨速','5分钟涨跌'], inplace=True)
        
        return process_dataframe(df.head(top_n), format=format)
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        return f"获取股票列表失败: {e}"


@cached(cache)
@retry_decorator
def get_concept_list(top_n: int = 20, format: Optional[Literal['markdown', 'json', 'dict']] = 'dict', exclude: Optional[str] = None) -> Union[str, pd.DataFrame]:
    """
    获取板块列表和实时交易数据
    
    Args:
        top_n: 返回的板块数量
        format: 返回格式，可选 'markdown', 'json', 'dict', None。如果为None，返回原始DataFrame
        exclude: 排除包含指定字符串的板块
    
    Returns:
        根据format参数返回相应格式的板块列表和实时交易数据，如果format为None则返回DataFrame
    """
    try:
        df = safe_akshare_call(ak.stock_board_concept_name_em)
        if exclude:
            df = df[df.板块名称.str.contains(exclude) == False]
        df = df[['板块名称', '板块代码', '最新价', '涨跌额', '涨跌幅', '换手率', '上涨家数', '下跌家数']].head(top_n)
        
        return process_dataframe(df, format=format)
    except Exception as e:
        logger.error(f"获取板块列表失败: {e}")
        return f"获取板块列表失败: {e}"


@cached(cache)
@retry_decorator
def get_concept_detail(concept_code: str, format: Optional[Literal['markdown', 'json', 'dict']] = 'dict') -> Union[str, dict]:
    """
    获取板块详情，并为涨停股票添加详细的涨停信息
    
    Args:
        concept_code: 板块代码, 示例：BK1128
        format: 返回格式，可选 'markdown', 'json', 'dict', None。如果为None，返回原始DataFrame
    
    Returns:
        根据format参数返回相应格式的板块详情，涨停股票包含详细涨停信息
    """
    try:
        # 获取板块成分股
        df = safe_akshare_call(ak.stock_board_industry_cons_em, symbol=concept_code)
        
        # 获取今日涨停股票数据
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
        
        # 初始化计数器和结果
        limitup_cnt_30 = 0
        limitup_cnt_20 = 0
        limitup_cnt_10 = 0
        
        if df is not None and not df.empty and limitup_df is not None and not limitup_df.empty:
            # 为涨停股票添加涨停信息
            def add_limitup_info(row):
                """为每行数据添加涨停信息"""
                nonlocal limitup_cnt_30, limitup_cnt_20, limitup_cnt_10
                
                stock_code = row['代码']
                
                # 查找该股票是否在涨停池中
                limitup_stock = limitup_df[limitup_df['代码'] == stock_code]
                
                if not limitup_stock.empty:
                    # 根据涨跌幅分类计数
                    try:
                        # 确保涨跌幅是数值类型
                        change_pct = float(row['涨跌幅'])
                        
                        if change_pct > 25:
                            limitup_cnt_30 += 1
                        elif change_pct > 15:
                            limitup_cnt_20 += 1
                        elif change_pct > 5:
                            limitup_cnt_10 += 1
                        else:
                            print(f'警告：涨停股票{stock_code}, 涨幅{change_pct}异常')
                    except (ValueError, TypeError) as e:
                        print(f'警告：无法解析股票{stock_code}的涨跌幅: {row.get("涨跌幅", "未知")}')
                    
                    # 获取涨停信息
                    limitup_info = limitup_stock.iloc[0]
                    
                    # 构建涨停情况字典
                    limitup_situation = {
                        '封板资金': int(limitup_info.get('封板资金', '0')),
                        '首次封板时间': _format_time(limitup_info.get('首次封板时间', '')),
                        '最后封板时间': _format_time(limitup_info.get('最后封板时间', '')),
                        '炸板次数': int(limitup_info.get('炸板次数', '0')),
                        '涨停统计': limitup_info.get('涨停统计', '未知'),
                        '连板数': int(limitup_info.get('连板数', '0'))
                    }
                    
                    # 将涨停情况添加到行数据中
                    row['涨停情况'] = limitup_situation
                    row['是否涨停'] = '是'
                else:
                    # 非涨停股票
                    row['涨停情况'] = None
                    row['是否涨停'] = '否'
                
                return row
        
            # 应用涨停信息添加函数
            df = df.apply(add_limitup_info, axis=1)
            
            # 重新排列列顺序，将涨停信息放在前面
            base_columns = ['代码', '名称', '是否涨停', '涨停情况']
            other_columns = [col for col in df.columns if col not in base_columns]
            df = df[base_columns + other_columns]
            
            # 构建完整结果
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
                # 如果没有涨停数据，仍然返回板块成分股，但不包含涨停信息
                df['是否涨停'] = '未知'
                df['涨停情况'] = None
                
                result['板块明细'] = process_dataframe(df, format=format, max_rows=300)
                return result
            else:
                return "数据获取异常"
    except Exception as e:
        logger.error(f"获取板块详情失败: {e}")
        return f"获取板块详情失败: {e}"
        
        
@cached(cache)
@retry_decorator
def get_stock_basic_info(stock_code: str, format: Optional[Literal['markdown', 'json', 'dict']] = 'dict') -> Union[str, dict]:
    """
    获取股票业务信息
    
    Args:
        stock_code: 股票代码
        format: 返回格式，可选 'markdown', 'json', 'dict', None。如果为None，返回原始DataFrame
    
    Returns:
        根据format参数返回相应格式的股票基本信息
    """
    try:
        # 参数验证
        if not validate_stock_code(stock_code):
            return "股票代码格式错误，应为6位数字"
        
        df = safe_akshare_call(ak.stock_profile_cninfo, stock_code)
        df1 = safe_akshare_call(ak.stock_individual_info_em, symbol=stock_code).set_index('item').T.to_dict(orient='records')
        
        df['总股本'] = df1[0]['总股本']
        df['流通股'] = df1[0]['流通股']
        df['流通市值'] = df1[0]['流通市值']
        df['总市值'] = df1[0]['总市值']
        df['行业'] = df1[0]['行业']

        return process_dataframe(df, format=format)[0] if format is not None else df
    except Exception as e:
        logger.error(f"获取股票基本信息失败: {e}")
        return f"获取股票基本信息失败: {e}"
