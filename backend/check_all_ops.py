# -*- coding: utf-8 -*-
import sqlite3
conn = sqlite3.connect('aps.db')
c = conn.cursor()

# 查询所有工序，看看 resource_id 的分布情况
c.execute('''
    SELECT o.status, COUNT(*), 
           SUM(CASE WHEN o.resource_id IS NOT NULL THEN 1 ELSE 0 END) as has_resource
    FROM operations o
    GROUP BY o.status
''')
print("Operations by status:")
print("Status | Count | Has Resource")
print("-" * 40)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]}")

print("\n" + "="*80 + "\n")

# 查看几个待排程工序的详细信息
c.execute('''
    SELECT o.id, po.order_number, o.sequence, o.name, o.resource_id, o.status
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    WHERE o.status = 'pending'
    LIMIT 10
''')
print("Sample pending operations:")
print("Op ID | Order | Seq | Name | Resource ID | Status")
print("-" * 70)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")

conn.close()
