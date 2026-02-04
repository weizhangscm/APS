# -*- coding: utf-8 -*-
"""
最终检查：所有工序的资源分配
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

print("=" * 80)
print("所有工序名称及其资源分配汇总")
print("=" * 80)

c.execute('''
    SELECT o.name as op_name, r.name as resource_name, COUNT(*) as count
    FROM operations o
    LEFT JOIN resources r ON o.resource_id = r.id
    GROUP BY o.name, r.name
    ORDER BY o.name, r.name
''')

print("{:<15} | {:<15} | {:>5}".format("工序名称", "资源", "数量"))
print("-" * 45)
for row in c.fetchall():
    print("{:<15} | {:<15} | {:>5}".format(
        row[0] if row[0] else 'NULL', 
        row[1] if row[1] else 'NULL', 
        row[2]
    ))

conn.close()
