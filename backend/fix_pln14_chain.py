# -*- coding: utf-8 -*-
"""
修复 PLN20260014 整个工序链的排程时间
工序30结束后，调整工序40、50、60的时间
"""
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('aps.db')
c = conn.cursor()

def calculate_end_time(start_time, duration_hours, capacity_per_day=8):
    """计算结束时间（考虑工作时间 8:00-16:00）"""
    remaining_hours = duration_hours
    current_time = start_time
    
    # 确保从工作时间开始
    if current_time.hour < 8:
        current_time = current_time.replace(hour=8, minute=0, second=0, microsecond=0)
    elif current_time.hour >= 16:
        current_time = (current_time + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
    
    while remaining_hours > 0:
        day_end = current_time.replace(hour=16, minute=0, second=0, microsecond=0)
        available_hours = (day_end - current_time).total_seconds() / 3600
        
        if available_hours <= 0:
            # 已过工作时间，移到下一天
            current_time = (current_time + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
            continue
        
        if available_hours >= remaining_hours:
            return current_time + timedelta(hours=remaining_hours)
        else:
            remaining_hours -= available_hours
            current_time = (current_time + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
    
    return current_time

def get_next_working_time(time):
    """获取下一个工作时间"""
    if time.hour < 8:
        return time.replace(hour=8, minute=0, second=0, microsecond=0)
    elif time.hour >= 16:
        return (time + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
    return time

# 获取订单ID
c.execute('''
    SELECT id FROM production_orders WHERE order_number = 'PLN20260014'
''')
order_id = c.fetchone()[0]

# 获取所有工序
c.execute('''
    SELECT o.id, o.sequence, o.name, o.run_time, o.scheduled_start, o.scheduled_end
    FROM operations o
    WHERE o.order_id = ?
    ORDER BY o.sequence
''', (order_id,))

operations = list(c.fetchall())

print("当前工序状态:")
for op in operations:
    print(f"  {op[1]} {op[2]}: run_time={op[3]}h")

# 从工序30开始重新计算时间链
# 工序30的开始时间已经设置好了
op30_idx = None
for i, op in enumerate(operations):
    if op[1] == 30:
        op30_idx = i
        break

if op30_idx is not None:
    # 获取工序30的结束时间
    op30 = operations[op30_idx]
    if op30[5]:
        prev_end = datetime.fromisoformat(op30[5].replace('T', ' ').split('.')[0])
    else:
        # 重新计算
        prev_end = datetime.fromisoformat('2026-02-06 15:18:00')
    
    print(f"\n从工序30结束时间 {prev_end} 开始调整后续工序:")
    
    # 调整工序40、50、60
    for i in range(op30_idx + 1, len(operations)):
        op = operations[i]
        op_id, seq, name, run_time, _, _ = op
        
        # 开始时间 = 前一个工序结束时间（调整到工作时间）
        start_time = get_next_working_time(prev_end)
        end_time = calculate_end_time(start_time, run_time)
        
        print(f"  {seq} {name}: {start_time} - {end_time} ({run_time}h)")
        
        # 更新数据库
        c.execute('''
            UPDATE operations 
            SET scheduled_start = ?, scheduled_end = ?, status = 'scheduled'
            WHERE id = ?
        ''', (start_time.isoformat(), end_time.isoformat(), op_id))
        
        prev_end = end_time
    
    conn.commit()

# 验证结果
print("\n" + "=" * 80)
print("更新后的工序状态:")
c.execute('''
    SELECT o.sequence, o.name, o.status, o.scheduled_start, o.scheduled_end, o.run_time
    FROM operations o
    WHERE o.order_id = ?
    ORDER BY o.sequence
''', (order_id,))

for row in c.fetchall():
    start = row[3][:16] if row[3] else '-'
    end = row[4][:16] if row[4] else '-'
    print(f"  {row[0]} {row[1]}: {start} - {end} ({row[5]}h) [{row[2]}]")

conn.close()
print("\n完成！")
