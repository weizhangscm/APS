# -*- coding: utf-8 -*-
import sqlite3
conn = sqlite3.connect('aps.db')
cursor = conn.cursor()

# 检查 CNC机床-3 上的订单的交货期和排程时间
cursor.execute("""
    SELECT po.order_number, po.due_date, o.name, o.sequence, 
           o.scheduled_start, o.scheduled_end, o.status, o.resource_id
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    WHERE o.resource_id = 3
    ORDER BY po.due_date
""")
results = cursor.fetchall()
print('CNC机床-3 (resource_id=3) 上的工序:')
print('订单号 | 交货期 | 工序 | 序号 | 排程开始 | 排程结束 | 状态 | resource_id')
print('-' * 100)
for r in results:
    print(f'{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} | {r[7]}')

conn.close()
