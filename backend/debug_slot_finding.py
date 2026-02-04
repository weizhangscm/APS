# -*- coding: utf-8 -*-
"""
调试时间槽查找问题
"""
from datetime import datetime, timedelta

# 模拟算法逻辑
def simulate_find_slot(duration_hours, earliest_start, capacity_per_day=8, planning_horizon=90):
    """模拟 _find_available_slot 的行为"""
    current_time = earliest_start
    max_iterations = planning_horizon * 3  # 270
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        day_start = current_time.replace(hour=8, minute=0, second=0, microsecond=0)
        if current_time.hour < 8:
            pass
        elif current_time.hour >= 17:
            day_start = (current_time + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
            current_time = day_start
        
        day_end = day_start + timedelta(hours=capacity_per_day)
        
        # 假设资源完全空闲（没有现有时间段）
        day_used = 0
        available_today = capacity_per_day - day_used  # = 8
        
        if available_today >= duration_hours:
            # 条件满足，可以排程
            slot_start = max(current_time, day_start)
            slot_end = slot_start + timedelta(hours=duration_hours)
            
            if slot_end <= day_end:
                return slot_start, slot_end, iteration
        
        # 移动到下一天
        current_time = (day_start + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
    
    # 回退到无限产能模式
    return earliest_start, earliest_start + timedelta(hours=duration_hours), -1

# 测试不同工序时长
print("测试不同工序时长在空闲资源上的排程结果：")
print("=" * 80)

earliest_start = datetime(2026, 2, 3, 18, 36, 15)  # 模拟当前时间

test_durations = [5.0, 8.0, 10.0, 13.6, 17.9, 22.3]

for duration in test_durations:
    start, end, iterations = simulate_find_slot(duration, earliest_start)
    print(f"工序时长: {duration:>5.1f}h => 排程到: {start.strftime('%Y-%m-%d %H:%M')} - {end.strftime('%Y-%m-%d %H:%M')} (迭代{iterations}次)")

print("\n" + "=" * 80)
print("问题分析：")
print("=" * 80)
print("当 duration_hours > capacity_per_day (8h) 时：")
print("  - 条件 'available_today >= duration_hours' 永远为 False")
print("  - 因为 available_today 最大也只有 8h")
print("  - 算法会遍历所有270天，然后回退到最早开始时间")
