# -*- coding: utf-8 -*-
"""
调试635天间隔问题
"""
from datetime import datetime, timedelta

# 检查635天是什么
print("635天 =", 635 / 365, "年")
print("635天 =", 635 / 30, "个月")

# 检查 planning_horizon * 3 = 90 * 3 = 270
# 但算法中有个问题：每次迭代移动一天，但条件永远不满足时会用完所有迭代

# 问题可能在：当工序时长 > 8小时时，算法会跳过270天
# 然后回退到earliest_start + duration

# 但这不能解释635天...

# 让我检查是否有多次调用
# 每次schedule_order会从上一个工序的结束时间开始
# 如果每次都跳过270天，那么第二个工序就会是270天后
# 第三个工序又是270天后...

print("\n模拟工序链排程：")
print("假设 planning_horizon = 90, max_iterations = 270")

# 但问题在于，每个工序都会独立调用 _find_available_slot
# 如果工序时长 > 8h，且当天产能不足，算法会一直迭代到 max_iterations
# 然后回退...

# 等等，让我重新看一下回退逻辑
# 第938-940行：
# end_time = earliest_start + timedelta(hours=duration_hours)
# return earliest_start, end_time

# 这是正确的！回退后应该从 earliest_start 开始
# 那为什么会有635天的间隔？

# 让我检查是否是资源冲突导致的
print("\n检查资源时间段冲突...")
print("PLN20260008 工序10在 钣金工位-2 (ID=10) 上排程")
print("开始: 2027-10-31 08:00")
print("结束: 2027-10-31 21:36")
print("时长: 13.6h")

print("\n下一个工序20的 earliest_start = 2027-10-31 21:36")
print("如果资源10在接下来270天内每天都被占满...")
print("算法会遍历270天后回退到 2027-10-31 21:36")

print("\n但实际排程到了 2029-07-28 08:00")
print("从 2027-10-31 到 2029-07-28 = ", (datetime(2029, 7, 28) - datetime(2027, 10, 31)).days, "天")

# 检查从哪里来的间隔
gap = datetime(2029, 7, 28) - datetime(2027, 10, 31)
print(f"\n间隔 = {gap.days} 天 = {gap.days / 30:.1f} 个月")

# 635天 = 270 + 365 = 1年 + 270天
# 或者 635 = 2 * 270 + 95
print(f"\n635 / 270 = {635 / 270:.2f}")
print(f"635 - 270 = {635 - 270}")
print(f"635 - 270*2 = {635 - 270*2}")

# 啊！问题可能是每次找时间段都会跳过270天
# 但冲突检测逻辑有问题，导致即使回退后仍然检测到冲突
# 然后再次跳过270天...
