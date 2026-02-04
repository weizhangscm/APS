# -*- coding: utf-8 -*-
"""
修复 PLN20260014 工序30（焊接）的排程数据

根据工序链：
- 工序20 折弯成型: 结束于 2026-02-04 19:17 - 2026-02-05 07:35
- 工序30 焊接: 应该从 2026-02-05 07:35 开始，持续 15.30 小时
- 工序40 喷涂: 开始于 2026-02-05 22:53

需要检查焊接工序能否在工序20结束后、工序40开始前完成
"""
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('aps.db')
c = conn.cursor()

# 获取订单ID
c.execute('''
    SELECT id FROM production_orders WHERE order_number = 'PLN20260014'
''')
order_id = c.fetchone()[0]

# 获取工序信息
c.execute('''
    SELECT o.id, o.sequence, o.name, o.run_time, o.scheduled_start, o.scheduled_end
    FROM operations o
    WHERE o.order_id = ?
    ORDER BY o.sequence
''', (order_id,))

operations = c.fetchall()
print("当前工序状态:")
for op in operations:
    print(f"  {op[1]} {op[2]}: run_time={op[3]}h, start={op[4]}, end={op[5]}")

# 找到工序20和工序30
op20 = None
op30 = None
op40 = None

for op in operations:
    if op[1] == 20:
        op20 = op
    elif op[1] == 30:
        op30 = op
    elif op[1] == 40:
        op40 = op

if op20 and op30:
    # 工序30应该从工序20结束后开始
    op20_end = datetime.fromisoformat(op20[5].split('.')[0])
    op30_run_time = op30[3]  # 15.30 小时
    
    # 计算工序30的开始和结束时间
    # 考虑工作时间（每天8:00-16:00，8小时）
    op30_start = op20_end
    
    # 如果工序20结束后已经超过工作时间，调整到下一个工作日
    if op30_start.hour >= 16:
        # 移到下一个工作日的8:00
        op30_start = op30_start.replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)
    elif op30_start.hour < 8:
        # 移到当天的8:00
        op30_start = op30_start.replace(hour=8, minute=0, second=0, microsecond=0)
    
    # 计算结束时间（考虑跨天）
    remaining_hours = op30_run_time
    current_time = op30_start
    
    while remaining_hours > 0:
        # 当天剩余工作时间
        day_end = current_time.replace(hour=16, minute=0, second=0, microsecond=0)
        available_hours = (day_end - current_time).total_seconds() / 3600
        
        if available_hours >= remaining_hours:
            # 可以在当天完成
            op30_end = current_time + timedelta(hours=remaining_hours)
            remaining_hours = 0
        else:
            # 需要跨天
            remaining_hours -= available_hours
            # 移到下一个工作日
            current_time = (current_time + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
    
    print(f"\n计算工序30排程:")
    print(f"  工序20结束: {op20_end}")
    print(f"  工序30开始: {op30_start}")
    print(f"  工序30持续: {op30_run_time} 小时")
    print(f"  工序30结束: {op30_end}")
    
    if op40:
        op40_start = datetime.fromisoformat(op40[4].split('.')[0])
        print(f"  工序40开始: {op40_start}")
        
        if op30_end > op40_start:
            print(f"\n警告: 工序30结束时间 ({op30_end}) 晚于工序40开始时间 ({op40_start})")
            print("需要调整后续工序的排程时间")
    
    # 更新工序30
    c.execute('''
        UPDATE operations 
        SET scheduled_start = ?, scheduled_end = ?, status = 'scheduled'
        WHERE id = ?
    ''', (op30_start.isoformat(), op30_end.isoformat(), op30[0]))
    
    conn.commit()
    print(f"\n已更新工序30: {op30_start} - {op30_end}, status=scheduled")

# 验证结果
print("\n" + "=" * 80)
print("更新后的工序状态:")
c.execute('''
    SELECT o.sequence, o.name, o.status, o.scheduled_start, o.scheduled_end
    FROM operations o
    WHERE o.order_id = ?
    ORDER BY o.sequence
''', (order_id,))

for row in c.fetchall():
    print(f"  {row[0]} {row[1]}: status={row[2]}, {row[3]} - {row[4]}")

conn.close()
print("\n完成！")
