from typing import Any,Optional
from datetime import datetime
from decimal import Decimal

def to_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None

def parse_timestamp(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value)
        except Exception:
            return None
    if isinstance(value, str):
        # try ISO first
        try:
            return datetime.fromisoformat(value)
        except Exception:
            pass
        # common fallback formats
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
            try:
                return datetime.strptime(value, fmt)
            except Exception:
                continue
    return None