# -*- coding: utf-8 -*-
import sqlite3
conn = sqlite3.connect('aps.db')
cursor = conn.cursor()

# 检查截图中显示的订单
orders_to_check = ['PLN20260035', 'PLN20260029', 'PLN20260022', 'PRD20260006']

for order_num in orders_to_check:
    cursor.execute("""
        SELECT o.id, o.name, o.sequence, o.resource_id, r.name as resource_name, o.status
        FROM operations o
        LEFT JOIN resources r ON o.resource_id = r.id
        JOIN production_orders po ON o.order_id = po.id
        WHERE po.order_number = ?
        ORDER BY o.sequence
    """, (order_num,))
    results = cursor.fetchall()
    print(f'\n{order_num} 的工序:')
    for r in results:
        print(f'  序号{r[2]} {r[1]}: resource_id={r[3]}, resource_name={r[4]}, status={r[5]}')

conn.close()
