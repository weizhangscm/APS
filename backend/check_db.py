# -*- coding: utf-8 -*-
import sqlite3
conn = sqlite3.connect('aps.db')
cursor = conn.cursor()

# 检查 CNC机床-3 的工序现在的状态
cursor.execute("""
    SELECT o.id, o.name, o.resource_id, r.name as resource_name, o.status, po.order_number
    FROM operations o
    LEFT JOIN resources r ON o.resource_id = r.id
    JOIN production_orders po ON o.order_id = po.id
    WHERE o.resource_id = 3
    ORDER BY po.order_number
""")
results = cursor.fetchall()
print('当前数据库中 CNC机床-3 (resource_id=3) 的工序:')
print(f'共 {len(results)} 个工序')
for r in results:
    print(f'  {r[5]} - {r[1]}: resource_id={r[2]}, status={r[4]}')

print('\n' + '='*50)

# 检查是否有工序被分配到 CNC机床-1 但原来可能在其他CNC机床
cursor.execute("""
    SELECT o.id, o.name, o.resource_id, o.status, po.order_number
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    WHERE o.resource_id = 1
    ORDER BY po.order_number
""")
results = cursor.fetchall()
print(f'\n当前数据库中 CNC机床-1 (resource_id=1) 的工序:')
print(f'共 {len(results)} 个工序')
for r in results:
    print(f'  {r[4]} - {r[1]}: resource_id={r[2]}, status={r[3]}')

conn.close()
