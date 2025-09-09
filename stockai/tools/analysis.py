

from typing import Dict, List


def _analyze_concept_overlap(concept1_stocks: List[Dict], concept2_stocks: List[Dict]) -> bool:
    """
    计算两个概念板块的重叠度
    
    Args:
        concept1_stocks: 第一个概念板块的股票列表
        concept2_stocks: 第二个概念板块的股票列表
    
    Returns:
        bool: 如果重叠度超过阈值返回True，否则返回False
    """
    if not concept1_stocks or not concept2_stocks:
        return False
    
    # 提取股票代码集合
    stocks1_codes = {stock['代码'] for stock in concept1_stocks if '代码' in stock}
    stocks2_codes = {stock['代码'] for stock in concept2_stocks if '代码' in stock}
    
    if not stocks1_codes or not stocks2_codes:
        return False
    
    # 计算交集
    intersection = stocks1_codes.intersection(stocks2_codes)
    
    # 计算重叠度（使用较小的概念作为分母）
    min_size = min(len(stocks1_codes), len(stocks2_codes))
    overlap_ratio = len(intersection) / min_size if min_size > 0 else 0
    
    return overlap_ratio

