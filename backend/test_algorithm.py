# -*- coding: utf-8 -*-
"""测试排程算法是否会改变已分配的 resource_id"""
import sqlite3

# 模拟检查：查看 PLN20260016 订单的工序在排程前后的 resource_id 变化
conn = sqlite3.connect('aps.db')
cursor = conn.cursor()

# 查看 PLN20260016 的工序
cursor.execute("""
    SELECT o.id, o.name, o.sequence, o.resource_id, r.name as resource_name, o.status
    FROM operations o
    LEFT JOIN resources r ON o.resource_id = r.id
    JOIN production_orders po ON o.order_id = po.id
    WHERE po.order_number = 'PLN20260016'
    ORDER BY o.sequence
""")
results = cursor.fetchall()
print('PLN20260016 的工序:')
print('op_id | name | seq | resource_id | resource_name | status')
print('-' * 80)
for r in results:
    print(f'{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]}')

# 检查 CNC机床-1 和 CNC机床-3 所属的工作中心
cursor.execute("""
    SELECT r.id, r.name, r.work_center_id, wc.name as wc_name
    FROM resources r
    JOIN work_centers wc ON r.work_center_id = wc.id
    WHERE r.name LIKE '%CNC%'
""")
results = cursor.fetchall()
print('\nCNC资源的工作中心:')
print('resource_id | resource_name | work_center_id | work_center_name')
print('-' * 80)
for r in results:
    print(f'{r[0]} | {r[1]} | {r[2]} | {r[3]}')

conn.close()
