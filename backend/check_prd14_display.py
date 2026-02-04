# -*- coding: utf-8 -*-
"""
检查 PRD20260014 在甘特图上应该如何显示
"""
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('aps.db')
c = conn.cursor()

c.execute('''
    SELECT order_number, due_date, confirmed_start, confirmed_end
    FROM production_orders
    WHERE order_number = 'PRD20260014'
''')

row = c.fetchone()
print("PRD20260014 订单信息:")
print(f"  交货期 (due_date): {row[1]}")
print(f"  确认开始 (confirmed_start): {row[2]}")
print(f"  确认结束 (confirmed_end): {row[3]}")

# 模拟后端甘特图逻辑
due_date_str = row[1]
if due_date_str:
    # 解析日期
    due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00').split('.')[0])
    display_start = due_date.replace(hour=8, minute=0, second=0)
    print(f"\n后端甘特图显示逻辑:")
    print(f"  display_start (使用交货日期 8:00): {display_start}")

c.execute('''
    SELECT o.sequence, o.name, o.run_time
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    WHERE po.order_number = 'PRD20260014'
    ORDER BY o.sequence
''')

print(f"\n工序显示时间计算:")
for row in c.fetchall():
    seq, name, run_time = row
    display_end = display_start + timedelta(hours=run_time)
    print(f"  {seq} {name}: {display_start.strftime('%m-%d %H:%M')} - {display_end.strftime('%m-%d %H:%M')} (duration: {run_time}h)")

conn.close()
