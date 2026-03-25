"""
资源/班次的「可排产」墙钟区间：按班次顺序与休息开始/结束挖空，不做休息时长分摊。
"""
from datetime import datetime, timedelta, time, date
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from .. import models
from ..services.location_catalog import (
    PRIMARY_LOCATION_CODE,
    matrix_location_for_resource,
    normalize_location_code,
)
from ..services.rest_breaks import hm_to_minutes

_DS_DEFAULT_START = "09:00"
_DS_DEFAULT_END = "18:00"


def _shifts_for_resource_filtered(db: Session, resource: models.Resource) -> List[models.Shift]:
    shifts = (
        db.query(models.Shift)
        .filter(models.Shift.resource_id == resource.id)
        .order_by(models.Shift.id)
        .all()
    )
    target = matrix_location_for_resource(resource)
    out: List[models.Shift] = []
    for s in shifts:
        sl = normalize_location_code(getattr(s, "location", None)) or PRIMARY_LOCATION_CODE
        if sl == target:
            out.append(s)
    return out


def _parse_operating_break_minutes(s: Optional[str]) -> int:
    if not s or not str(s).strip():
        return 0
    s = str(s).strip()
    if ":" in s:
        return int(round(hm_to_minutes(s)))
    try:
        return int(float(s))
    except ValueError:
        return 0


def segment_templates_for_resource(
    db: Session, resource_id: int
) -> List[Tuple[str, str, Optional[str], Optional[str], int]]:
    """
    每个模板: (shift_start, shift_end, rest_start|None, rest_end|None, break_mins_fallback)。
    有班次时 rest 取 break_start_time/break_end_time；无班次取 operating_rest_*。
    break_mins_fallback：未配置休息起止时用于从班次末尾扣除（兼容旧数据）。
    """
    resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    if not resource:
        return [(_DS_DEFAULT_START, _DS_DEFAULT_END, None, None, 0)]
    shifts = _shifts_for_resource_filtered(db, resource)
    if shifts:
        tpl = []
        for s in shifts:
            rs = (getattr(s, "break_start_time", None) or "").strip() or None
            re = (getattr(s, "break_end_time", None) or "").strip() or None
            tpl.append(
                (s.start_time, s.end_time, rs, re, int(s.break_time or 0))
            )
        return tpl
    st = (resource.operating_start or "").strip() or _DS_DEFAULT_START
    et = (resource.operating_end or "").strip() or _DS_DEFAULT_END
    ors = (getattr(resource, "operating_rest_start", None) or "").strip() or None
    ore = (getattr(resource, "operating_rest_end", None) or "").strip() or None
    brk = _parse_operating_break_minutes(getattr(resource, "operating_break", None))
    return [(st, et, ors, ore, brk)]


def _shift_wall_bounds(d0: date, start_str: str, end_str: str) -> Tuple[datetime, datetime]:
    sm = hm_to_minutes(start_str)
    em = hm_to_minutes(end_str)
    d_mid = datetime.combine(d0, time.min)
    ws = d_mid + timedelta(minutes=sm)
    if em > sm:
        we = d_mid + timedelta(minutes=em)
    else:
        we = d_mid + timedelta(days=1) + timedelta(minutes=em)
    return ws, we


def _rest_bounds_in_shift_wall(
    ws: datetime, we: datetime, rest_start_hm: str, rest_end_hm: str
) -> Optional[Tuple[datetime, datetime]]:
    """休息区间锚在班次墙钟内；开始、结束时刻相对 ws 所在日历日推算并夹到 [ws, we]。"""
    sm = int(hm_to_minutes(rest_start_hm))
    em = int(hm_to_minutes(rest_end_hm))
    base = datetime.combine(ws.date(), time.min)
    rs_dt = base + timedelta(minutes=sm)
    re_dt = base + timedelta(minutes=em)
    if rs_dt < ws:
        rs_dt += timedelta(days=1)
        re_dt += timedelta(days=1)
    if re_dt <= rs_dt:
        re_dt += timedelta(days=1)
    rs_c = max(rs_dt, ws)
    re_c = min(re_dt, we)
    if re_c > rs_c:
        return rs_c, re_c
    return None


def productive_segments_one_template_on_day(
    d0: date,
    shift_start: str,
    shift_end: str,
    rest_start: Optional[str],
    rest_end: Optional[str],
    break_mins_fallback: int,
) -> List[Tuple[datetime, datetime]]:
    ws, we = _shift_wall_bounds(d0, shift_start, shift_end)
    if we <= ws:
        return []
    rs = (rest_start or "").strip() or None
    re = (rest_end or "").strip() or None
    if rs and re:
        rb = _rest_bounds_in_shift_wall(ws, we, rs, re)
        if rb:
            rs_c, re_c = rb
            out: List[Tuple[datetime, datetime]] = []
            if rs_c > ws:
                out.append((ws, rs_c))
            if we > re_c:
                out.append((re_c, we))
            return [(a, b) for a, b in out if b > a]
        return [(ws, we)]
    if break_mins_fallback and break_mins_fallback > 0:
        prod_end = we - timedelta(minutes=break_mins_fallback)
        if prod_end > ws:
            return [(ws, prod_end)]
    return [(ws, we)]


def _merge_segments(segs: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
    if not segs:
        return []
    segs = sorted(segs, key=lambda x: x[0])
    merged: List[Tuple[datetime, datetime]] = []
    cs, ce = segs[0]
    for s, e in segs[1:]:
        if s <= ce:
            ce = max(ce, e)
        else:
            merged.append((cs, ce))
            cs, ce = s, e
    merged.append((cs, ce))
    return merged


def productive_segments_starting_on_day(
    db: Session, resource_id: int, day_date: date
) -> List[Tuple[datetime, datetime]]:
    """在给定「班次起始日」上，所有模板的可排产区间并集（已合并相邻）。"""
    all_s: List[Tuple[datetime, datetime]] = []
    for tpl in segment_templates_for_resource(db, resource_id):
        all_s.extend(productive_segments_one_template_on_day(day_date, *tpl))
    return _merge_segments(all_s)


def daily_productive_hours_for_resource(db: Session, resource_id: int) -> float:
    """典型一日的可排产小时数（用于产能/排序等）。"""
    d = date(2026, 1, 5)
    segs = productive_segments_starting_on_day(db, resource_id, d)
    h = sum((e - s).total_seconds() / 3600.0 for s, e in segs)
    return round(h, 2) if h > 0 else 9.0


def productive_hours_in_datetime_range(
    db: Session, resource_id: int, interval_start: datetime, interval_end: datetime
) -> float:
    """[interval_start, interval_end) 与可排产区间的交集小时数（KPI 等）。"""
    if interval_end <= interval_start:
        return 0.0
    total = 0.0
    d = interval_start.date()
    end_d = interval_end.date()
    while d <= end_d:
        for s, e in productive_segments_starting_on_day(db, resource_id, d):
            cs = max(s, interval_start)
            ce = min(e, interval_end)
            if ce > cs:
                total += (ce - cs).total_seconds() / 3600.0
        d += timedelta(days=1)
    return round(total, 2)
