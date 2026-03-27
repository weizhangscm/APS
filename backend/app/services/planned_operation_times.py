"""
计划订单工序的初始排程时刻：与详细计划表/利用率一致，按资源当日可排产时段（班次或 operating_start/end，否则 DS 默认）取「首段开始」，结束 = 开始 + run_time。
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from .working_segments import productive_segments_starting_on_day


def first_productive_instant_on_day(db: Session, resource_id: int, day: date) -> datetime:
    """资源在指定日历日的第一个可排产时刻（墙钟）。"""
    segs = productive_segments_starting_on_day(db, resource_id, day)
    if segs:
        return segs[0][0]
    return datetime.combine(day, time(9, 0))


def planned_operation_scheduled_times(
    db: Session,
    resource_id: Optional[int],
    due_date: datetime,
    run_time_hours: float,
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    为计划订单工序生成初始 scheduled_start / scheduled_end。
    无资源或无效工时时返回 (None, None)。
    """
    if resource_id is None:
        return None, None
    try:
        rt = float(run_time_hours)
    except (TypeError, ValueError):
        return None, None
    if rt <= 0:
        return None, None

    day = due_date.date() if isinstance(due_date, datetime) else due_date
    start = first_productive_instant_on_day(db, int(resource_id), day)
    end = start + timedelta(hours=rt)
    return start, end
