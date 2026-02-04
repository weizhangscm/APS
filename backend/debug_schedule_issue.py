# -*- coding: utf-8 -*-
"""
调试排程问题：为什么工序被排到2027年以后
"""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('aps.db')
c = conn.cursor()

print("=" * 80)
print("1. 查看资源的每日产能设置")
print("=" * 80)
c.execute('SELECT id, name, capacity_per_day, work_center_id FROM resources ORDER BY id')
print("Resource ID | Name | Capacity/Day | WC ID")
print("-" * 60)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")

print("\n" + "=" * 80)
print("2. 查看各资源上排程的工序数量和时间范围")
print("=" * 80)
c.execute('''
    SELECT r.id, r.name, 
           COUNT(o.id) as op_count,
           MIN(o.scheduled_start) as earliest,
           MAX(o.scheduled_end) as latest,
           SUM(o.run_time) as total_hours
    FROM resources r
    LEFT JOIN operations o ON r.id = o.resource_id AND o.scheduled_start IS NOT NULL
    GROUP BY r.id
    ORDER BY r.id
''')
print("Res ID | Name | Op Count | Earliest | Latest | Total Hours")
print("-" * 100)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")

print("\n" + "=" * 80)
print("3. 查看2026年2月每天各资源的排程工时")
print("=" * 80)
c.execute('''
    SELECT date(o.scheduled_start) as day, 
           r.name as resource_name,
           COUNT(o.id) as op_count,
           SUM(o.run_time) as total_hours
    FROM operations o
    JOIN resources r ON o.resource_id = r.id
    WHERE o.scheduled_start >= '2026-02-01' AND o.scheduled_start < '2026-03-01'
    GROUP BY day, r.id
    ORDER BY day, r.id
''')
print("Day | Resource | Op Count | Total Hours")
print("-" * 60)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")

print("\n" + "=" * 80)
print("4. 检查被排到2027年的具体订单和工序")
print("=" * 80)
c.execute('''
    SELECT po.order_number, po.due_date, po.status,
           o.sequence, o.name, o.run_time,
           r.name as resource_name,
           o.scheduled_start, o.scheduled_end
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    JOIN resources r ON o.resource_id = r.id
    WHERE o.scheduled_start > '2026-03-31'
    ORDER BY po.order_number, o.sequence
''')
print("Order | Due Date | Status | Seq | Op Name | Run Time | Resource | Start | End")
print("-" * 120)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]} | {row[7]} | {row[8]}")

print("\n" + "=" * 80)
print("5. 检查特定资源(冲床-1, ID=7)的排程密度")
print("=" * 80)
c.execute('''
    SELECT date(o.scheduled_start) as day,
           COUNT(o.id) as op_count,
           SUM(o.run_time) as total_hours,
           GROUP_CONCAT(po.order_number) as orders
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    WHERE o.resource_id = 7 AND o.scheduled_start IS NOT NULL
    GROUP BY day
    ORDER BY day
    LIMIT 30
''')
print("Day | Op Count | Total Hours | Orders")
print("-" * 80)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3][:50] if row[3] else ''}")

print("\n" + "=" * 80)
print("6. 计算各资源的总需求工时 vs 可用产能")
print("=" * 80)
c.execute('''
    SELECT r.id, r.name, r.capacity_per_day,
           COUNT(o.id) as total_ops,
           COALESCE(SUM(o.run_time), 0) as total_demand_hours
    FROM resources r
    LEFT JOIN operations o ON r.id = o.resource_id
    GROUP BY r.id
    ORDER BY r.id
''')
print("Res ID | Name | Cap/Day | Total Ops | Demand Hours | Days Needed (at full cap)")
print("-" * 90)
for row in c.fetchall():
    cap = row[2] if row[2] else 8
    demand = row[4] if row[4] else 0
    days_needed = demand / cap if cap > 0 else 0
    print(f"{row[0]} | {row[1]} | {cap} | {row[3]} | {demand:.1f} | {days_needed:.1f}")

conn.close()
