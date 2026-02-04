# -*- coding: utf-8 -*-
import sqlite3
conn = sqlite3.connect('aps.db')
cursor = conn.cursor()

# 查看 CNC 相关资源
cursor.execute("SELECT id, name FROM resources WHERE name LIKE '%CNC%'")
resources = cursor.fetchall()
print('CNC相关资源:')
for r in resources:
    print(f'  ID={r[0]}, Name={r[1]}')

# 查看分配到 CNC机床-3 (假设ID是某个值) 的工序
for resource_id, resource_name in resources:
    if 'CNC机床-3' in resource_name:
        cursor.execute("""
            SELECT o.id, o.order_id, o.name, o.sequence, o.resource_id, o.status, po.order_number
            FROM operations o
            JOIN production_orders po ON o.order_id = po.id
            WHERE o.resource_id = ?
            ORDER BY po.order_number
        """, (resource_id,))
        results = cursor.fetchall()
        print(f'\n分配到 {resource_name} (resource_id={resource_id}) 的工序:')
        print('op_id | order_id | name | seq | resource_id | status | order_number')
        print('-' * 80)
        for r in results:
            print(f'{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]}')

conn.close()
