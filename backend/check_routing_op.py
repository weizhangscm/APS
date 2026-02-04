# -*- coding: utf-8 -*-
"""
检查工序与工艺路线工序的关联
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

print("=" * 80)
print("检查所有订单中 routing_operation_id 为空的工序")
print("=" * 80)

c.execute('''
    SELECT po.order_number, o.sequence, o.name, o.routing_operation_id
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    WHERE o.routing_operation_id IS NULL
    ORDER BY po.order_number, o.sequence
''')

rows = c.fetchall()
if rows:
    print("发现 routing_operation_id 为空的工序:")
    for row in rows:
        print(f"  {row[0]} - {row[1]} {row[2]}: routing_operation_id = {row[3]}")
else:
    print("没有发现 routing_operation_id 为空的工序")

print("\n" + "=" * 80)
print("检查 PLN20260014 的所有工序")
print("=" * 80)

c.execute('''
    SELECT o.sequence, o.name, o.routing_operation_id, o.status
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    WHERE po.order_number = 'PLN20260014'
    ORDER BY o.sequence
''')

for row in c.fetchall():
    print(f"  {row[0]} {row[1]}: routing_operation_id={row[2]}, status={row[3]}")

print("\n" + "=" * 80)
print("检查工艺路线工序表中的焊接工序")
print("=" * 80)

c.execute('''
    SELECT ro.id, ro.name, ro.sequence, r.name as routing_name, wc.name as work_center
    FROM routing_operations ro
    JOIN routings r ON ro.routing_id = r.id
    JOIN work_centers wc ON ro.work_center_id = wc.id
    WHERE ro.name = '焊接'
''')

for row in c.fetchall():
    print(f"  ID {row[0]}: {row[1]} (seq {row[2]}) in {row[3]}, WC: {row[4]}")

conn.close()
