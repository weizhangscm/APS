# -*- coding: utf-8 -*-
"""
检查钣金车间的工序排程问题
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

print("=" * 80)
print("钣金车间 (WC 2) 的资源")
print("=" * 80)

c.execute('''
    SELECT id, name FROM resources WHERE work_center_id = 2
''')
for row in c.fetchall():
    print(f"  ID {row[0]}: {row[1]}")

print("\n" + "=" * 80)
print("问题工序的 resource_id 分析")
print("=" * 80)

# 检查问题工序的 resource_id
problem_orders = [
    ('PLN20260002', 30), ('PLN20260003', 20), ('PLN20260006', 20),
    ('PLN20260008', 20), ('PLN20260009', 30), ('PLN20260013', 30),
    ('PLN20260014', 30), ('PLN20260031', 20), ('PLN20260032', 20),
    ('PLN20260033', 20)
]

for order_num, seq in problem_orders:
    c.execute('''
        SELECT o.sequence, o.name, o.resource_id, o.status, r.name
        FROM operations o
        JOIN production_orders po ON o.order_id = po.id
        LEFT JOIN resources r ON o.resource_id = r.id
        WHERE po.order_number = ? AND o.sequence = ?
    ''', (order_num, seq))
    
    row = c.fetchone()
    if row:
        print(f"  {order_num} - {row[0]} {row[1]}: resource_id={row[2]} ({row[4]}), status={row[3]}")

print("\n" + "=" * 80)
print("检查排程算法如何处理这些工序")
print("=" * 80)

# 检查这些问题工序的 routing_operation 中的 work_center_id
print("\n问题工序的工艺路线信息:")
for order_num, seq in problem_orders:
    c.execute('''
        SELECT o.sequence, o.name, o.resource_id, o.routing_operation_id, 
               ro.work_center_id, r.name as assigned_resource
        FROM operations o
        JOIN production_orders po ON o.order_id = po.id
        JOIN routing_operations ro ON o.routing_operation_id = ro.id
        LEFT JOIN resources r ON o.resource_id = r.id
        WHERE po.order_number = ? AND o.sequence = ?
    ''', (order_num, seq))
    
    row = c.fetchone()
    if row:
        print(f"  {order_num} - {row[0]} {row[1]}:")
        print(f"    resource_id: {row[2]} ({row[5]})")
        print(f"    routing_op work_center_id: {row[4]}")
        
        # 检查 routing_op 的 work_center_id 对应的资源
        c.execute('''
            SELECT id, name FROM resources WHERE work_center_id = ?
        ''', (row[4],))
        wc_resources = c.fetchall()
        print(f"    该工作中心的资源: {wc_resources}")

conn.close()
