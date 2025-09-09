from dataclasses import dataclass


@dataclass
class AkshareConfig:
    # 缓存配置
    cache_maxsize: int = 128
    cache_ttl: int = 600

    # 重试配置
    max_retries: int = 3
    retry_wait_min: float = 1.0
    retry_wait_max: float = 10.0

    # 数据配置
    default_max_rows: int = 120
    default_lookback_days: int = 365

    # 涨停阈值（备用，部分逻辑暂未完全替换硬编码）
    limitup_threshold_30: float = 25.0
    limitup_threshold_20: float = 15.0
    limitup_threshold_10: float = 5.0


config = AkshareConfig()


