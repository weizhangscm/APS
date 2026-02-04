# -*- coding: utf-8 -*-
"""
测试修复后的排程算法
"""
from datetime import datetime, timedelta

# 模拟新的算法逻辑
def get_next_working_time(dt, capacity_per_day=8):
    work_start_hour = 8
    work_end_hour = work_start_hour + int(capacity_per_day)
    
    if dt.hour < work_start_hour:
        return dt.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
    elif dt.hour >= work_end_hour:
        next_day = dt + timedelta(days=1)
        return next_day.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
    else:
        return dt

def calculate_end_time(start_time, duration_hours, capacity_per_day=8):
    work_start_hour = 8
    work_end_hour = work_start_hour + int(capacity_per_day)
    
    remaining_hours = duration_hours
    current_time = start_time
    
    max_days = 365
    days_checked = 0
    
    while remaining_hours > 0 and days_checked < max_days:
        days_checked += 1
        
        if current_time.hour < work_start_hour:
            current_time = current_time.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
        elif current_time.hour >= work_end_hour:
            current_time = (current_time + timedelta(days=1)).replace(
                hour=work_start_hour, minute=0, second=0, microsecond=0
            )
            continue
        
        day_end = current_time.replace(hour=work_end_hour, minute=0, second=0, microsecond=0)
        available_hours_today = (day_end - current_time).total_seconds() / 3600
        
        if remaining_hours <= available_hours_today:
            end_time = current_time + timedelta(hours=remaining_hours)
            return end_time, days_checked
        else:
            remaining_hours -= available_hours_today
            current_time = (current_time + timedelta(days=1)).replace(
                hour=work_start_hour, minute=0, second=0, microsecond=0
            )
    
    return start_time + timedelta(hours=duration_hours), -1

# 测试不同工序时长
print("=" * 80)
print("测试修复后的排程算法（允许跨天）")
print("=" * 80)

earliest_start = datetime(2026, 2, 3, 18, 36, 15)  # 18:36 已经超过工作时间

test_durations = [5.0, 8.0, 10.0, 13.6, 17.9, 22.3, 50.0]

print(f"\n最早开始时间: {earliest_start.strftime('%Y-%m-%d %H:%M')}")
print(f"每日产能: 8小时 (08:00-16:00)")
print("\n" + "-" * 80)
print(f"{'工序时长':>10} | {'开始时间':>20} | {'结束时间':>20} | {'跨越天数':>10}")
print("-" * 80)

for duration in test_durations:
    # 先获取下一个工作时间
    slot_start = get_next_working_time(earliest_start, 8)
    # 计算结束时间
    slot_end, days = calculate_end_time(slot_start, duration, 8)
    
    print(f"{duration:>10.1f}h | {slot_start.strftime('%Y-%m-%d %H:%M'):>20} | {slot_end.strftime('%Y-%m-%d %H:%M'):>20} | {days:>10}")

print("\n" + "=" * 80)
print("测试工序链排程（模拟 PLN20260008 的6道工序）")
print("=" * 80)

# 模拟 PLN20260008 的工序链
operations = [
    ("10 冲压下料", 13.6),
    ("20 折弯成型", 17.9),
    ("30 焊接", 22.3),
    ("40 喷涂", 13.4),
    ("50 检测", 8.9),
    ("60 包装", 4.5),
]

current_time = datetime(2026, 2, 3, 18, 36, 15)
print(f"\n订单开始时间: {current_time.strftime('%Y-%m-%d %H:%M')}")
print("\n" + "-" * 100)
print(f"{'工序':>15} | {'时长':>8} | {'开始时间':>20} | {'结束时间':>20} | {'跨天数':>8}")
print("-" * 100)

for op_name, duration in operations:
    slot_start = get_next_working_time(current_time, 8)
    slot_end, days = calculate_end_time(slot_start, duration, 8)
    
    print(f"{op_name:>15} | {duration:>7.1f}h | {slot_start.strftime('%Y-%m-%d %H:%M'):>20} | {slot_end.strftime('%Y-%m-%d %H:%M'):>20} | {days:>8}")
    
    # 下一个工序从上一个工序结束后开始
    current_time = slot_end

print("\n" + "=" * 80)
print(f"订单总完成时间: {current_time.strftime('%Y-%m-%d %H:%M')}")
total_days = (current_time - datetime(2026, 2, 3, 18, 36, 15)).days
print(f"总耗时: {total_days} 天")
print("=" * 80)
