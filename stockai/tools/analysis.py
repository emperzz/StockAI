
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Literal, Optional, Union
from itertools import combinations
from scipy.stats import pearsonr, spearmanr
from .akshare.market_data import get_concept_stocks_list, get_code_or_name, get_stock_kline


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

def calculate_vector_similarity(vector1: List[float], 
                               vector2: List[float], 
                               method: Literal['cosine', 'euclidean', 'dot_product'] = 'cosine') -> float:
    """
    计算两个向量的相似度
    
    这个函数用于计算embedding.py中创建的两个向量之间的相似度。
    支持三种计算方式：
    1. 余弦相似度：衡量向量方向的相似性，范围[-1, 1]，值越大越相似
    2. 欧几里得距离：衡量向量间的距离，值越小越相似
    3. 点积：衡量向量的相关性，值越大越相关
    
    Args:
        vector1 (List[float]): 第一个向量，通常是embedding.py生成的向量
        vector2 (List[float]): 第二个向量，通常是embedding.py生成的向量
        method (str): 相似度计算方法，可选 'cosine'(余弦相似度), 'euclidean'(欧几里得距离), 'dot_product'(点积)
    
    Returns:
        float: 相似度值
        
    Raises:
        ValueError: 当向量为空或长度不匹配时
        ValueError: 当计算方法不支持时
    
    Example:
        # 使用embedding.py生成两个向量
        from app.embedding import EmbeddingService
        
        embedding_service = EmbeddingService()
        vector1 = embedding_service.embed_query("你好世界")
        vector2 = embedding_service.embed_query("hello world")
        
        # 计算余弦相似度
        similarity = calculate_vector_similarity(vector1, vector2, 'cosine')
        print(f"余弦相似度: {similarity}")
        
        # 计算欧几里得距离
        distance = calculate_vector_similarity(vector1, vector2, 'euclidean')
        print(f"欧几里得距离: {distance}")
    """
    # 输入验证
    if not vector1 or not vector2:
        raise ValueError("向量不能为空")
    
    if len(vector1) != len(vector2):
        raise ValueError(f"向量长度不匹配: vector1长度{len(vector1)}, vector2长度{len(vector2)}")
    
    # 转换为numpy数组，提高计算效率
    v1 = np.array(vector1, dtype=np.float64)
    v2 = np.array(vector2, dtype=np.float64)
    
    if method == 'cosine':
        # 余弦相似度计算
        # 公式: cos(θ) = (v1 · v2) / (||v1|| * ||v2||)
        # 其中 · 表示点积，||v|| 表示向量的模长
        
        # 计算点积
        dot_product = np.dot(v1, v2)
        
        # 计算两个向量的模长
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        # 避免除零错误
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        
        # 计算余弦相似度
        cosine_similarity = dot_product / (norm_v1 * norm_v2)
        
        # 确保结果在[-1, 1]范围内，处理浮点数精度问题
        return np.clip(cosine_similarity, -1.0, 1.0)
    
    elif method == 'euclidean':
        # 欧几里得距离计算
        # 公式: d = √(Σ(v1[i] - v2[i])²)
        
        # 计算向量差的平方和
        squared_diff = np.sum((v1 - v2) ** 2)
        
        # 开平方根得到欧几里得距离
        euclidean_distance = np.sqrt(squared_diff)
        
        return float(euclidean_distance)
    
    elif method == 'dot_product':
        # 点积计算
        # 公式: v1 · v2 = Σ(v1[i] * v2[i])
        
        dot_product = np.dot(v1, v2)
        return float(dot_product)
    
    else:
        raise ValueError(f"不支持的计算方法: {method}，请使用 'cosine', 'euclidean' 或 'dot_product'")


def calculate_multiple_similarities(vector1: List[float], 
                                  vectors: List[List[float]], 
                                  method: Literal['cosine', 'euclidean', 'dot_product'] = 'cosine') -> List[float]:
    """
    计算一个向量与多个向量的相似度
    
    这个函数用于批量计算相似度，比如计算一个查询向量与多个文档向量的相似度。
    
    Args:
        vector1 (List[float]): 基准向量
        vectors (List[List[float]]): 要比较的向量列表
        method (str): 相似度计算方法
    
    Returns:
        List[float]: 相似度值列表，与输入向量列表顺序对应
        
    Example:
        # 计算一个查询向量与多个文档向量的相似度
        query_vector = embedding_service.embed_query("查询文本")
        doc_vectors = [
            embedding_service.embed_query("文档1"),
            embedding_service.embed_query("文档2"),
            embedding_service.embed_query("文档3")
        ]
        
        similarities = calculate_multiple_similarities(query_vector, doc_vectors, 'cosine')
        for i, sim in enumerate(similarities):
            print(f"文档{i+1}相似度: {sim}")
    """
    similarities = []
    
    for vector in vectors:
        try:
            sim = calculate_vector_similarity(vector1, vector, method)
            similarities.append(sim)
        except Exception as e:
            # 如果某个向量计算出错，记录错误并继续
            print(f"计算相似度时出错: {e}")
            similarities.append(0.0)  # 出错时返回0
    
    return similarities


def calculate_kline_similarity(kline_data1: Union[pd.DataFrame, List[Dict], Dict[str, List]], 
                              kline_data2: Union[pd.DataFrame, List[Dict], Dict[str, List]], 
                              method: Literal['pearson', 'spearman', 'both'] = 'both',
                              price_column: str = 'close') -> Dict[str, Any]:
    """
    计算两只股票K线数据的相似度
    
    这个函数用于计算两只股票K线数据之间的相似度，支持Pearson和Spearman相关系数。
    K线数据可以包含开盘价、收盘价、最高价、最低价、成交量等信息。
    
    Args:
        kline_data1: 第一只股票的K线数据，支持DataFrame、字典列表或字典格式
        kline_data2: 第二只股票的K线数据，支持DataFrame、字典列表或字典格式
        method: 相似度计算方法，可选 'pearson'(皮尔逊相关系数), 'spearman'(斯皮尔曼相关系数), 'both'(两者都计算)
        price_column: 用于计算相似度的价格列名，默认为'close'(收盘价)
    
    Returns:
        Dict[str, Any]: 包含相似度结果的字典
        - 如果method='pearson': {'pearson_correlation': float, 'pearson_pvalue': float}
        - 如果method='spearman': {'spearman_correlation': float, 'spearman_pvalue': float}
        - 如果method='both': 包含上述所有字段
        
    Raises:
        ValueError: 当数据格式不支持或数据为空时
        ValueError: 当价格列不存在时
        ValueError: 当计算方法不支持时
    
    Example:
        # 使用DataFrame格式的K线数据
        import pandas as pd
        
        # 假设有两个股票的K线数据
        stock1_data = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'open': [100, 102, 101],
            'high': [105, 108, 106],
            'low': [98, 100, 99],
            'close': [103, 106, 104],
            'volume': [1000, 1200, 1100]
        })
        
        stock2_data = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'open': [50, 51, 50.5],
            'high': [52, 54, 53],
            'low': [49, 50, 49.5],
            'close': [51, 53, 52],
            'volume': [2000, 2400, 2200]
        })
        
        # 计算Pearson相关系数
        result = calculate_kline_similarity(stock1_data, stock2_data, 'pearson')
        print(f"Pearson相关系数: {result['pearson_correlation']}")
        
        # 计算Spearman相关系数
        result = calculate_kline_similarity(stock1_data, stock2_data, 'spearman')
        print(f"Spearman相关系数: {result['spearman_correlation']}")
        
        # 同时计算两种相关系数
        result = calculate_kline_similarity(stock1_data, stock2_data, 'both')
        print(f"Pearson: {result['pearson_correlation']}, Spearman: {result['spearman_correlation']}")
    """
    # 数据预处理：将不同格式的数据统一转换为DataFrame
    df1 = _preprocess_kline_data(kline_data1)
    df2 = _preprocess_kline_data(kline_data2)
    
    # 验证数据
    if df1.empty or df2.empty:
        raise ValueError("K线数据不能为空")
    
    # 检查价格列是否存在
    if price_column not in df1.columns:
        raise ValueError(f"第一只股票数据中不存在价格列: {price_column}")
    if price_column not in df2.columns:
        raise ValueError(f"第二只股票数据中不存在价格列: {price_column}")
    
    # 提取价格数据
    prices1 = df1[price_column].values
    prices2 = df2[price_column].values
    
    # 确保两个价格序列长度相同
    min_length = min(len(prices1), len(prices2))
    if min_length < 2:
        raise ValueError("价格数据至少需要2个数据点才能计算相关系数")
    
    prices1 = prices1[:min_length]
    prices2 = prices2[:min_length]
    
    # 移除NaN值
    valid_mask = ~(np.isnan(prices1) | np.isnan(prices2))
    if np.sum(valid_mask) < 2:
        raise ValueError("有效价格数据点不足，无法计算相关系数")
    
    prices1_clean = prices1[valid_mask]
    prices2_clean = prices2[valid_mask]
    
    result = {}
    
    # 计算Pearson相关系数
    if method in ['pearson', 'both']:
        try:
            pearson_corr, pearson_pvalue = pearsonr(prices1_clean, prices2_clean)
            result['pearson_correlation'] = float(pearson_corr)
            result['pearson_pvalue'] = float(pearson_pvalue)
        except Exception as e:
            result['pearson_correlation'] = None
            result['pearson_pvalue'] = None
            print(f"计算Pearson相关系数时出错: {e}")
    
    # 计算Spearman相关系数
    if method in ['spearman', 'both']:
        try:
            spearman_corr, spearman_pvalue = spearmanr(prices1_clean, prices2_clean)
            result['spearman_correlation'] = float(spearman_corr)
            result['spearman_pvalue'] = float(spearman_pvalue)
        except Exception as e:
            result['spearman_correlation'] = None
            result['spearman_pvalue'] = None
            print(f"计算Spearman相关系数时出错: {e}")
    
    # 添加元数据
    result['data_points'] = len(prices1_clean)
    result['price_column'] = price_column
    
    return result


def _preprocess_kline_data(kline_data: Union[pd.DataFrame, List[Dict], Dict[str, List]]) -> pd.DataFrame:
    """
    预处理K线数据，将不同格式统一转换为DataFrame
    
    Args:
        kline_data: K线数据，支持多种格式
        
    Returns:
        pd.DataFrame: 标准化的DataFrame格式K线数据
        
    Raises:
        ValueError: 当数据格式不支持时
    """
    if isinstance(kline_data, pd.DataFrame):
        # 已经是DataFrame，直接返回
        return kline_data.copy()
    
    elif isinstance(kline_data, list):
        # 字典列表格式
        if not kline_data:
            return pd.DataFrame()
        
        # 检查是否为字典列表
        if not all(isinstance(item, dict) for item in kline_data):
            raise ValueError("列表中的元素必须是字典格式")
        
        return pd.DataFrame(kline_data)
    
    elif isinstance(kline_data, dict):
        # 字典格式，键为列名，值为数据列表
        if not kline_data:
            return pd.DataFrame()
        
        # 检查所有值是否为列表
        if not all(isinstance(value, list) for value in kline_data.values()):
            raise ValueError("字典格式中所有值必须是列表")
        
        # 检查所有列表长度是否相同
        lengths = [len(value) for value in kline_data.values()]
        if len(set(lengths)) > 1:
            raise ValueError("字典格式中所有列表长度必须相同")
        
        return pd.DataFrame(kline_data)
    
    else:
        raise ValueError(f"不支持的数据格式: {type(kline_data)}，请使用DataFrame、字典列表或字典格式")


def calculate_multiple_kline_similarities(reference_kline: Union[pd.DataFrame, List[Dict], Dict[str, List]], 
                                         kline_list: List[Union[pd.DataFrame, List[Dict], Dict[str, List]]], 
                                         method: Literal['pearson', 'spearman', 'both'] = 'both',
                                         price_column: str = 'close') -> List[Dict[str, Any]]:
    """
    计算一只股票与多只股票K线数据的相似度
    
    这个函数用于批量计算K线相似度，比如计算一只基准股票与多只候选股票的相似度。
    
    Args:
        reference_kline: 基准股票的K线数据
        kline_list: 要比较的股票K线数据列表
        method: 相似度计算方法
        price_column: 用于计算相似度的价格列名
    
    Returns:
        List[Dict[str, Any]]: 相似度结果列表，与输入股票列表顺序对应
        
    Example:
        # 计算一只基准股票与多只股票的相似度
        reference_stock = get_stock_kline_data("000001")  # 基准股票
        candidate_stocks = [
            get_stock_kline_data("000002"),
            get_stock_kline_data("000003"),
            get_stock_kline_data("000004")
        ]
        
        similarities = calculate_multiple_kline_similarities(
            reference_stock, candidate_stocks, 'both'
        )
        
        for i, sim in enumerate(similarities):
            print(f"股票{i+1}相似度:")
            print(f"  Pearson: {sim.get('pearson_correlation', 'N/A')}")
            print(f"  Spearman: {sim.get('spearman_correlation', 'N/A')}")
    """
    similarities = []
    
    for i, kline_data in enumerate(kline_list):
        try:
            sim = calculate_kline_similarity(reference_kline, kline_data, method, price_column)
            similarities.append(sim)
        except Exception as e:
            # 如果某个股票计算出错，记录错误并继续
            print(f"计算股票{i+1}的K线相似度时出错: {e}")
            # 创建默认结果
            default_result = {'data_points': 0, 'price_column': price_column}
            if method in ['pearson', 'both']:
                default_result.update({'pearson_correlation': None, 'pearson_pvalue': None})
            if method in ['spearman', 'both']:
                default_result.update({'spearman_correlation': None, 'spearman_pvalue': None})
            similarities.append(default_result)
    
    return similarities


def analyze_kline_similarity_trend(similarities: List[Dict[str, Any]], 
                                  method: Literal['pearson', 'spearman'] = 'pearson',
                                  threshold: float = 0.7) -> Dict[str, Any]:
    """
    分析K线相似度趋势
    
    这个函数用于分析多只股票的K线相似度分布情况，找出高相似度股票。
    
    Args:
        similarities: 相似度结果列表
        method: 分析方法，基于哪种相关系数
        threshold: 高相似度阈值
    
    Returns:
        Dict[str, Any]: 分析结果
        - high_similarity_count: 高相似度股票数量
        - high_similarity_indices: 高相似度股票索引列表
        - average_similarity: 平均相似度
        - max_similarity: 最大相似度
        - min_similarity: 最小相似度
        
    Example:
        similarities = calculate_multiple_kline_similarities(reference, candidates, 'both')
        analysis = analyze_kline_similarity_trend(similarities, 'pearson', 0.8)
        print(f"高相似度股票数量: {analysis['high_similarity_count']}")
        print(f"平均相似度: {analysis['average_similarity']:.3f}")
    """
    if not similarities:
        return {
            'high_similarity_count': 0,
            'high_similarity_indices': [],
            'average_similarity': 0.0,
            'max_similarity': 0.0,
            'min_similarity': 0.0
        }
    
    # 提取相关系数
    correlation_key = f'{method}_correlation'
    correlations = []
    
    for sim in similarities:
        if correlation_key in sim and sim['data_points'] > 0:
            correlations.append(sim[correlation_key])
        else:
            correlations.append(0.0)
    
    correlations = np.array(correlations)
    
    # 计算统计信息
    high_similarity_mask = np.abs(correlations) >= threshold
    high_similarity_indices = np.where(high_similarity_mask)[0].tolist()
    
    result = {
        'high_similarity_count': int(np.sum(high_similarity_mask)),
        'high_similarity_indices': high_similarity_indices,
        'average_similarity': float(np.mean(correlations)),
        'max_similarity': float(np.max(correlations)),
        'min_similarity': float(np.min(correlations)),
        'threshold': threshold,
        'method': method
    }
    
    return result


def calculate_stock_kline_similarities(reference_stock: str, 
                                     stock_list: List[str], 
                                     start_date: Optional[str] = None, 
                                     end_date: Optional[str] = None, 
                                     period: Literal['1', '5', '15', '30', '60', 'daily', 'weekly'] = 'daily',
                                     method: Literal['pearson', 'spearman', 'both'] = 'both',
                                     price_column: str = '收盘') -> Dict[str, Any]:
    """
    计算一只参考股票与多只股票的K线相似度
    
    这个函数通过获取股票的K线数据，然后计算相似度。
    
    Args:
        reference_stock: 参考股票代码
        stock_list: 要比较的股票代码列表
        start_date: 开始日期，格式YYYY-MM-DD
        end_date: 结束日期，格式YYYY-MM-DD
        period: 数据周期，'1'|'5'|'15'|'30'|'60'|'daily'|'weekly'。
        method: 相似度计算方法
        price_column: 用于计算相似度的价格列名
    
    Returns:
        Dict[str, Any]: 包含分析结果的字典
        {
            "status": "success/error",
            "message": "结果描述",
            "reference_stock": "参考股票代码",
            "period": "数据周期",
            "start_date": "开始日期",
            "end_date": "结束日期",
            "method": "计算方法",
            "similarities": [
                {
                    "stock_code": "股票代码",
                    "pearson_correlation": 0.85,
                    "spearman_correlation": 0.82,
                    "data_points": 100,
                    "price_column": "close"
                }
            ],
            "failed_stocks": ["失败股票代码列表"]  # 可选
        }
        
    Example:
        # 计算贵州茅台与多只股票的相似度
        result = calculate_stock_kline_similarities(
            reference_stock="600519",
            stock_list=["000001", "000002", "000858"],
            start_date="2024-01-01",
            end_date="2024-01-31",
            period="daily",
            method="both"
        )
        
        if result["status"] == "success":
            for sim in result["similarities"]:
                print(f"股票 {sim['stock_code']} 相似度: {sim['pearson_correlation']:.3f}")
    """
    try:
        # 获取参考股票的K线数据
        reference_kline = get_stock_kline(reference_stock, start_date = start_date, end_date = end_date, period = period, format = None)
        if reference_kline is None or reference_kline.empty:
            return {
                "status": "error",
                "message": f"无法获取参考股票 {reference_stock} 的K线数据",
                "reference_stock": reference_stock,
                "similarities": []
            }
        
        # 获取所有股票的K线数据
        kline_data_list = []
        valid_stocks = []
        failed_stocks = []
        
        for stock_code in stock_list:
            try:
                kline_data = get_stock_kline(stock_code, start_date = start_date, end_date = end_date, period = '1', format = None)
                if kline_data is not None and not kline_data.empty:
                    kline_data_list.append(kline_data)
                    valid_stocks.append(stock_code)
                else:
                    failed_stocks.append(stock_code)
            except Exception as e:
                failed_stocks.append(stock_code)
        
        if not kline_data_list:
            return {
                "status": "error",
                "message": "无法获取任何股票的K线数据",
                "reference_stock": reference_stock,
                "similarities": [],
                "failed_stocks": failed_stocks
            }
        
        # 计算相似度
        similarities = calculate_multiple_kline_similarities(
            reference_kline, kline_data_list, method, price_column
        )
        
        # 构建结果
        result = {
            "status": "success",
            "message": f"成功计算 {len(valid_stocks)} 只股票的相似度",
            "reference_stock": reference_stock,
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "method": method,
            "similarities": []
        }
        
        # 添加相似度结果
        for i, stock_code in enumerate(valid_stocks):
            similarity_result = similarities[i].copy()
            similarity_result['stock_code'] = stock_code
            result["similarities"].append(similarity_result)
        
        # 添加失败股票信息
        if failed_stocks:
            result["failed_stocks"] = failed_stocks
            result["message"] += f"，{len(failed_stocks)} 只股票获取失败"
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"计算过程中发生错误: {str(e)}",
            "reference_stock": reference_stock,
            "similarities": []
        }