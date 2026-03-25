"""休息开始/结束时间与休息时长（分钟、operating_break 字符串）的换算。"""
from typing import Optional


def hm_to_minutes(time_str: Optional[str]) -> float:
    """'HH:mm' 或 'HH:mm:ss' 转为从 0 点起的分钟数（可含小数秒）。"""
    if not time_str:
        return 0.0
    parts = str(time_str).strip().split(":")
    h = int(parts[0]) if len(parts) > 0 else 0
    m = int(parts[1]) if len(parts) > 1 else 0
    sec = int(parts[2]) if len(parts) > 2 else 0
    return h * 60 + m + sec / 60


def break_minutes_between(start_hm: str, end_hm: str) -> int:
    """休息开始、结束（同日墙钟，结束可跨日）之间的分钟数。"""
    sm = int(hm_to_minutes(start_hm))
    em = int(hm_to_minutes(end_hm))
    if em <= sm:
        em += 24 * 60
    return max(0, em - sm)


def operating_break_duration_str(total_minutes: int) -> str:
    """写入资源 operating_break：与 DS 一致的 HH:MM:SS 时长表示。"""
    total_minutes = max(0, int(total_minutes))
    h, m = divmod(total_minutes, 60)
    return f"{h:02d}:{m:02d}:00"
