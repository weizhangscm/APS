# -*- coding: utf-8 -*-
"""
修复所有不一致的订单：
- 订单状态为 scheduled 但有工序状态为 pending 的情况
"""
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('aps.db')
c = conn.cursor()

def get_next_working_time(dt, capacity_per_day=8):
    """获取下一个工作时间点"""
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
    """计算结束时间（考虑跨天）"""
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
            current_time = (current_time + timedelta(days=1)).replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
            continue
        
        day_end = current_time.replace(hour=work_end_hour, minute=0, second=0, microsecond=0)
        available_hours = (day_end - current_time).total_seconds() / 3600
        
        if available_hours <= 0:
            current_time = (current_time + timedelta(days=1)).replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
            continue
        
        if available_hours >= remaining_hours:
            return current_time + timedelta(hours=remaining_hours)
        else:
            remaining_hours -= available_hours
            current_time = (current_time + timedelta(days=1)).replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
    
    return current_time

# 找到所有不一致的订单
c.execute('''
    SELECT DISTINCT po.id, po.order_number
    FROM production_orders po
    JOIN operations o ON o.order_id = po.id
    WHERE po.status = 'scheduled' 
      AND o.status = 'pending'
    ORDER BY po.order_number
''')

inconsistent_orders = c.fetchall()

print(f"发现 {len(inconsistent_orders)} 个需要修复的订单\n")

for order_id, order_number in inconsistent_orders:
    print(f"修复订单 {order_number}:")
    
    # 获取该订单的所有工序
    c.execute('''
        SELECT o.id, o.sequence, o.name, o.run_time, o.status, o.scheduled_start, o.scheduled_end
        FROM operations o
        WHERE o.order_id = ?
        ORDER BY o.sequence
    ''', (order_id,))
    
    operations = list(c.fetchall())
    
    # 找到pending工序并修复
    for i, op in enumerate(operations):
        op_id, seq, name, run_time, status, start, end = op
        
        if status != 'pending':
            continue
        
        print(f"  修复工序 {seq} {name}:")
        
        # 找前一个工序的结束时间
        prev_end = None
        for j in range(i - 1, -1, -1):
            if operations[j][6]:  # scheduled_end
                prev_end = datetime.fromisoformat(operations[j][6].replace('T', ' ').split('.')[0])
                break
        
        # 找后一个工序的开始时间
        next_start = None
        for j in range(i + 1, len(operations)):
            if operations[j][5]:  # scheduled_start
                next_start = datetime.fromisoformat(operations[j][5].replace('T', ' ').split('.')[0])
                break
        
        if prev_end:
            # 从前一个工序结束后开始
            op_start = get_next_working_time(prev_end)
            op_end = calculate_end_time(op_start, run_time)
            
            print(f"    从前序工序结束后开始: {op_start} - {op_end}")
            
            # 检查是否与后续工序冲突
            if next_start and op_end > next_start:
                print(f"    警告: 与后续工序冲突，需要调整后续工序")
                # 调整后续工序
                current_end = op_end
                for j in range(i + 1, len(operations)):
                    next_op = operations[j]
                    next_op_id, next_seq, next_name, next_run_time, _, _, _ = next_op
                    
                    next_op_start = get_next_working_time(current_end)
                    next_op_end = calculate_end_time(next_op_start, next_run_time)
                    
                    c.execute('''
                        UPDATE operations 
                        SET scheduled_start = ?, scheduled_end = ?, status = 'scheduled'
                        WHERE id = ?
                    ''', (next_op_start.isoformat(), next_op_end.isoformat(), next_op_id))
                    
                    print(f"    调整工序 {next_seq} {next_name}: {next_op_start} - {next_op_end}")
                    current_end = next_op_end
            
            # 更新当前工序
            c.execute('''
                UPDATE operations 
                SET scheduled_start = ?, scheduled_end = ?, status = 'scheduled'
                WHERE id = ?
            ''', (op_start.isoformat(), op_end.isoformat(), op_id))
        else:
            print(f"    无法确定开始时间（没有前序工序）")
    
    print()

conn.commit()

# 验证结果
print("=" * 80)
print("验证修复结果")
print("=" * 80)

c.execute('''
    SELECT DISTINCT po.order_number
    FROM production_orders po
    JOIN operations o ON o.order_id = po.id
    WHERE po.status = 'scheduled' 
      AND o.status = 'pending'
''')

remaining = c.fetchall()
if remaining:
    print(f"仍有 {len(remaining)} 个订单存在不一致")
    for row in remaining:
        print(f"  {row[0]}")
else:
    print("所有订单已修复！")

conn.close()
