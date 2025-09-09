import logging
from time import perf_counter
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .config import config


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


retry_decorator = retry(
    stop=stop_after_attempt(config.max_retries),
    wait=wait_exponential(multiplier=1, min=config.retry_wait_min, max=config.retry_wait_max),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    reraise=True,
)


def safe_akshare_call(api_func, *args, **kwargs):
    start = perf_counter()
    try:
        logger.info(f"调用AKShare API: {api_func.__name__} params={{{'args': args, 'kwargs': kwargs}}}")
        result = api_func(*args, **kwargs)
        elapsed = (perf_counter() - start) * 1000
        logger.info(f"API调用成功: {api_func.__name__}, 耗时: {elapsed:.1f}ms")
        return result
    except Exception as e:
        elapsed = (perf_counter() - start) * 1000
        logger.error(f"API调用失败: {api_func.__name__}, 耗时: {elapsed:.1f}ms, 错误: {e}")
        raise


