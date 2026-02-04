# -*- coding: utf-8 -*-
"""
检查CNC相关工序的资源分配
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

print("=" * 80)
print("资源列表")
print("=" * 80)
c.execute('SELECT id, name FROM resources ORDER BY id')
for row in c.fetchall():
    print(f"  ID {row[0]}: {row[1]}")

print("\n" + "=" * 80)
print("CNC相关工序")
print("=" * 80)

c.execute('''
    SELECT o.name, r.id, r.name, COUNT(*) as count
    FROM operations o
    LEFT JOIN resources r ON o.resource_id = r.id
    WHERE o.name LIKE '%CNC%' OR o.name LIKE '%车%'
    GROUP BY o.name, r.id
    ORDER BY o.name
''')

for row in c.fetchall():
    print(f"  {row[0]} -> Resource ID {row[1]}: {row[2]} (count: {row[3]})")

conn.close()
