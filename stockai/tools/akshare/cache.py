from cachetools import TTLCache
from .config import config


cache = TTLCache(maxsize=config.cache_maxsize, ttl=config.cache_ttl)


