# -*- coding: utf-8 -*-
"""
检查 PLN20260014 订单和工序状态
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

print("=" * 80)
print("检查 PLN20260014 订单状态")
print("=" * 80)

c.execute('''
    SELECT order_number, order_type, status, due_date
    FROM production_orders
    WHERE order_number = 'PLN20260014'
''')

row = c.fetchone()
if row:
    print(f"订单号: {row[0]}")
    print(f"类型: {row[1]}")
    print(f"订单状态: {row[2]}")
    print(f"交货期: {row[3]}")

print("\n工序详情:")
c.execute('''
    SELECT o.sequence, o.name, o.status, o.scheduled_start, o.scheduled_end, r.name
    FROM operations o
    LEFT JOIN resources r ON o.resource_id = r.id
    JOIN production_orders po ON o.order_id = po.id
    WHERE po.order_number = 'PLN20260014'
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

conn.close()
