

from typing import Dict, List, Union
from itertools import combinations
from .akshare.market_data import get_concept_stocks_list, get_code_or_name


def _analyze_concept_overlap(concept1_stocks: List[Dict], concept2_stocks: List[Dict]) -> Dict[str, Union[float, int, set]]:
    """
    计算两个概念板块的重叠度
    
    Args:
        concept1_stocks: 第一个概念板块的股票列表
        concept2_stocks: 第二个概念板块的股票列表
    
    Returns:
        Dict: 包含重叠度、交集、各板块股票数量的详细信息
    """
    if not concept1_stocks or not concept2_stocks:
        return {
            'overlap_ratio': 0.0,
            'intersection_count': 0,
            'concept1_count': 0,
            'concept2_count': 0,
            'intersection_codes': set()
        }
    
    # 提取股票代码集合
    stocks1_codes = {stock['代码'] for stock in concept1_stocks if '代码' in stock}
    stocks2_codes = {stock['代码'] for stock in concept2_stocks if '代码' in stock}
    
    if not stocks1_codes or not stocks2_codes:
        return {
            'overlap_ratio': 0.0,
            'intersection_count': 0,
            'concept1_count': len(stocks1_codes),
            'concept2_count': len(stocks2_codes),
            'intersection_codes': set()
        }
    
    # 计算交集
    intersection = stocks1_codes.intersection(stocks2_codes)
    
    # 计算重叠度（使用较小的概念作为分母）
    min_size = min(len(stocks1_codes), len(stocks2_codes))
    overlap_ratio = len(intersection) / min_size if min_size > 0 else 0.0
    
    return {
        'overlap_ratio': overlap_ratio,
        'intersection_count': len(intersection),
        'concept1_count': len(stocks1_codes),
        'concept2_count': len(stocks2_codes),
        'intersection_codes': intersection
    }


def analyze_concepts_overlap(concept_list: List[str], 
                           sort_by_overlap: bool = True,
                           include_overlap_stocks: bool = False) -> Dict[str, Union[str, List[Dict], Dict]]:
    """
    分析概念板块列表中的两两重叠度
    
    Args:
        concept_list: 概念板块代码列表
        sort_by_overlap: 是否按重叠度排序
        include_overlap_stocks: 是否包含重叠股票详情
    
    Returns:
        Dict: 包含分析结果的字典，格式如下：
        {
            "status": "success/partial/error",
            "message": "分析结果描述",
            "statistics": {
                "total_concepts": 3,
                "successful_concepts": 3,
                "failed_concepts": 0,
                "total_pairs": 3,
                "max_overlap": 0.25,
                "min_overlap": 0.0,
                "avg_overlap": 0.125
            },
            "overlap_pairs": [
                {
                    "concept1_code": "BK0001",
                    "concept1_name": "人工智能",
                    "concept2_code": "BK0002", 
                    "concept2_name": "芯片概念",
                    "overlap_ratio": 0.25,
                    "overlap_count": 5,
                    "concept1_count": 20,
                    "concept2_count": 30,
                    "overlap_stocks": ["000001", "000002"]  # 可选
                }
            ]
        }
    """
    try:
        if not concept_list or len(concept_list) < 2:
            return {
                "status": "error",
                "message": "需要至少2个板块代码进行分析",
                "statistics": {},
                "overlap_pairs": []
            }
        
        # 获取所有板块的股票清单（支持部分成功）
        concept_stocks_data = {}
        concept_names = {}
        failed_concepts = []
        
        for concept_code in concept_list:
            try:
                # 获取板块名称
                concept_name = get_code_or_name('concept', code=concept_code)
                if concept_name.startswith("未找到") or concept_name.startswith("解析失败"):
                    concept_name = f"未知板块({concept_code})"
                concept_names[concept_code] = concept_name
                
                # 获取板块股票清单
                stocks_data = get_concept_stocks_list(concept_code, format='dict')
                if isinstance(stocks_data, list):
                    concept_stocks_data[concept_code] = stocks_data
                else:
                    failed_concepts.append(concept_code)
                    
            except Exception as e:
                failed_concepts.append(concept_code)
        
        # 检查是否有足够的成功板块
        successful_concepts = list(concept_stocks_data.keys())
        if len(successful_concepts) < 2:
            return {
                "status": "error",
                "message": f"成功获取的板块数量不足，成功: {len(successful_concepts)}, 失败: {len(failed_concepts)}",
                "statistics": {
                    "total_concepts": len(concept_list),
                    "successful_concepts": len(successful_concepts),
                    "failed_concepts": len(failed_concepts)
                },
                "overlap_pairs": []
            }
        
        # 计算两两重叠度
        overlap_results = []
        
        for concept1_code, concept2_code in combinations(successful_concepts, 2):
            try:
                concept1_stocks = concept_stocks_data[concept1_code]
                concept2_stocks = concept_stocks_data[concept2_code]
                
                # 计算重叠度（现在返回详细信息）
                overlap_data = _analyze_concept_overlap(concept1_stocks, concept2_stocks)
                
                overlap_result = {
                    "concept1_code": concept1_code,
                    "concept1_name": concept_names[concept1_code],
                    "concept2_code": concept2_code,
                    "concept2_name": concept_names[concept2_code],
                    "overlap_ratio": round(overlap_data['overlap_ratio'], 4),
                    "overlap_count": overlap_data['intersection_count'],
                    "concept1_count": overlap_data['concept1_count'],
                    "concept2_count": overlap_data['concept2_count']
                }
                
                # 可选：包含重叠股票详情
                if include_overlap_stocks:
                    overlap_result["overlap_stocks"] = list(overlap_data['intersection_codes'])
                
                overlap_results.append(overlap_result)
                
            except Exception as e:
                overlap_results.append({
                    "concept1_code": concept1_code,
                    "concept1_name": concept_names.get(concept1_code, "未知"),
                    "concept2_code": concept2_code,
                    "concept2_name": concept_names.get(concept2_code, "未知"),
                    "overlap_ratio": 0.0,
                    "overlap_count": 0,
                    "concept1_count": 0,
                    "concept2_count": 0,
                    "error": str(e)
                })
        
        # 按重叠度排序
        if sort_by_overlap:
            overlap_results.sort(key=lambda x: x['overlap_ratio'], reverse=True)
        
        # 计算统计信息
        overlap_ratios = [r['overlap_ratio'] for r in overlap_results if 'error' not in r]
        statistics = {
            "total_concepts": len(concept_list),
            "successful_concepts": len(successful_concepts),
            "failed_concepts": len(failed_concepts),
            "total_pairs": len(overlap_results),
            "max_overlap": max(overlap_ratios) if overlap_ratios else 0.0,
            "min_overlap": min(overlap_ratios) if overlap_ratios else 0.0,
            "avg_overlap": sum(overlap_ratios) / len(overlap_ratios) if overlap_ratios else 0.0
        }
        
        # 确定状态
        if len(failed_concepts) == 0:
            status = "success"
            message = f"成功分析 {len(successful_concepts)} 个板块的 {len(overlap_results)} 对重叠关系"
        else:
            status = "partial"
            message = f"部分成功：分析 {len(successful_concepts)} 个板块的 {len(overlap_results)} 对重叠关系，{len(failed_concepts)} 个板块失败"
        
        return {
            "status": status,
            "message": message,
            "statistics": statistics,
            "overlap_pairs": overlap_results
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"分析过程中发生错误: {str(e)}",
            "statistics": {},
            "overlap_pairs": []
        }

