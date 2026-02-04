# -*- coding: utf-8 -*-
"""
检查为什么有些工序的 resource_id 是空的
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

print("=" * 80)
print("1. 统计 resource_id 为空的工序")
print("=" * 80)

c.execute('''
    SELECT COUNT(*) as total,
           SUM(CASE WHEN resource_id IS NULL THEN 1 ELSE 0 END) as null_count,
           SUM(CASE WHEN resource_id IS NOT NULL THEN 1 ELSE 0 END) as has_value
    FROM operations
''')
row = c.fetchone()
print(f"总工序数: {row[0]}")
print(f"resource_id 为空: {row[1]}")
print(f"resource_id 有值: {row[2]}")

print("\n" + "=" * 80)
print("2. 按订单类型统计 resource_id 为空的情况")
print("=" * 80)

c.execute('''
    SELECT po.order_type, 
           COUNT(*) as total,
           SUM(CASE WHEN o.resource_id IS NULL THEN 1 ELSE 0 END) as null_count
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    GROUP BY po.order_type
''')
print("Order Type | Total Ops | Null resource_id")
print("-" * 50)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]}")

print("\n" + "=" * 80)
print("3. 按订单统计 resource_id 为空的工序")
print("=" * 80)

c.execute('''
    SELECT po.order_number, po.order_type,
           COUNT(*) as total,
           SUM(CASE WHEN o.resource_id IS NULL THEN 1 ELSE 0 END) as null_count
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    GROUP BY po.order_number
    HAVING null_count > 0
    ORDER BY po.order_type, po.order_number
''')
print("Order | Type | Total Ops | Null resource_id")
print("-" * 60)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")

print("\n" + "=" * 80)
print("4. 检查 PLN20260008 的工序详情")
print("=" * 80)

c.execute('''
    SELECT o.id, o.sequence, o.name, o.resource_id, o.status, o.scheduled_start
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    WHERE po.order_number = 'PLN20260008'
    ORDER BY o.sequence
''')
print("Op ID | Seq | Name | Resource ID | Status | Start")
print("-" * 80)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")

conn.close()

print("\n" + "=" * 80)
print("分析：")
print("=" * 80)
print("""
可能的原因：
1. reset_and_reschedule.py 脚本在重新排程时，没有保留之前设置的 resource_id
2. 排程算法在某些情况下清除了 resource_id
3. 只有排程成功的工序才会设置 resource_id，未排程的工序 resource_id 被清空了
""")
