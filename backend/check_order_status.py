# -*- coding: utf-8 -*-
"""
检查订单和工序的状态
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

print("=" * 80)
print("检查 PRD20260014 订单状态")
print("=" * 80)

c.execute('''
    SELECT order_number, order_type, status, due_date, confirmed_start, confirmed_end
    FROM production_orders
    WHERE order_number = 'PRD20260014'
''')

row = c.fetchone()
if row:
    print(f"订单号: {row[0]}")
    print(f"类型: {row[1]}")
    print(f"状态: {row[2]}")
    print(f"交货期: {row[3]}")
    print(f"确认开始: {row[4]}")
    print(f"确认结束: {row[5]}")

print("\n工序详情:")
c.execute('''
    SELECT o.sequence, o.name, o.status, o.scheduled_start, o.scheduled_end, r.name
    FROM operations o
    LEFT JOIN resources r ON o.resource_id = r.id
    JOIN production_orders po ON o.order_id = po.id
    WHERE po.order_number = 'PRD20260014'
    ORDER BY o.sequence
''')

print("{:<5} | {:<12} | {:<10} | {:<20} | {:<20} | {}".format(
    "Seq", "Name", "Status", "Scheduled Start", "Scheduled End", "Resource"
))
print("-" * 100)
for row in c.fetchall():
    print("{:<5} | {:<12} | {:<10} | {:<20} | {:<20} | {}".format(
        row[0], row[1], row[2], 
        str(row[3]) if row[3] else '-',
        str(row[4]) if row[4] else '-',
        row[5] if row[5] else '-'
    ))

print("\n" + "=" * 80)
print("订单状态统计")
print("=" * 80)

c.execute('''
    SELECT order_type, status, COUNT(*) as count
    FROM production_orders
    GROUP BY order_type, status
    ORDER BY order_type, status
''')

for row in c.fetchall():
    print(f"  {row[0]} - {row[1]}: {row[2]}")

print("\n" + "=" * 80)
print("工序状态统计")
print("=" * 80)

c.execute('''
    SELECT o.status, 
           SUM(CASE WHEN o.scheduled_start IS NOT NULL THEN 1 ELSE 0 END) as has_schedule,
           COUNT(*) as total
    FROM operations o
    GROUP BY o.status
''')

print("{:<12} | {:>15} | {:>10}".format("Status", "Has Schedule", "Total"))
print("-" * 45)
for row in c.fetchall():
    print("{:<12} | {:>15} | {:>10}".format(row[0], row[1], row[2]))

conn.close()
