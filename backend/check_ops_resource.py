# -*- coding: utf-8 -*-
import sqlite3
conn = sqlite3.connect('aps.db')
c = conn.cursor()

# 查询 PLN20260009 的工序及其资源
c.execute('''
    SELECT o.sequence, o.name, o.resource_id, r.name as resource_name, o.status,
           o.scheduled_start, o.scheduled_end
    FROM operations o
    LEFT JOIN resources r ON o.resource_id = r.id
    JOIN production_orders po ON o.order_id = po.id
    WHERE po.order_number = 'PLN20260009'
    ORDER BY o.sequence
''')
print("PLN20260009 operations:")
print("Seq | Name | Resource ID | Resource Name | Status | Start | End")
print("-" * 80)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]}")

conn.close()
