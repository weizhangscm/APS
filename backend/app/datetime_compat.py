"""与数据库存储一致的 naive UTC datetime 处理。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    API（Pydantic/FastAPI）可能解析出带 tz 的 datetime，而库内与 SQLite 使用 naive UTC。
    统一转为 naive UTC，避免与 scheduled_start 等字段比较时触发
    \"can't compare offset-naive and offset-aware datetimes\"。
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)
