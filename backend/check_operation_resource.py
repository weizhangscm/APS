# -*- coding: utf-8 -*-
"""
检查工序表中的资源信息是否正确加载
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

print("=" * 80)
print("检查 PRD20260010 的工序资源")
print("=" * 80)

c.execute('''
    SELECT o.id, o.sequence, o.name, o.resource_id, r.name as resource_name
    FROM operations o
    LEFT JOIN resources r ON o.resource_id = r.id
    JOIN production_orders po ON o.order_id = po.id
    WHERE po.order_number = 'PRD20260010'
    ORDER BY o.sequence
''')

print("Op ID | Seq | Op Name | Resource ID | Resource Name")
print("-" * 80)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")

conn.close()
