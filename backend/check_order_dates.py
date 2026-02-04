# -*- coding: utf-8 -*-
"""
查询订单的计划时间分布
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

# 1. 查询所有订单的基本信息和交货日期
print("=" * 80)
print("订单交货日期分布:")
print("=" * 80)
c.execute('''
    SELECT order_number, order_type, status, due_date, product_id
    FROM production_orders
    ORDER BY due_date
''')
print("Order Number | Type | Status | Due Date | Product ID")
print("-" * 80)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")

# 2. 查询工序的排程时间分布
print("\n" + "=" * 80)
print("工序排程开始时间分布 (按月统计):")
print("=" * 80)
c.execute('''
    SELECT strftime('%Y-%m', scheduled_start) as month, COUNT(*) as count
    FROM operations
    WHERE scheduled_start IS NOT NULL
    GROUP BY month
    ORDER BY month
''')
print("Month | Count")
print("-" * 40)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]}")

# 3. 查询2026年3月31日之后开始的工序
print("\n" + "=" * 80)
print("2026-03-31 之后排程的工序:")
print("=" * 80)
c.execute('''
    SELECT po.order_number, o.sequence, o.name, o.scheduled_start, o.scheduled_end, o.status
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    WHERE o.scheduled_start > '2026-03-31'
    ORDER BY o.scheduled_start
    LIMIT 30
''')
print("Order | Seq | Name | Start | End | Status")
print("-" * 100)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")

# 4. 查询订单交货日期在2026-03-31之后的订单
print("\n" + "=" * 80)
print("交货日期在 2026-03-31 之后的订单:")
print("=" * 80)
c.execute('''
    SELECT order_number, order_type, status, due_date
    FROM production_orders
    WHERE due_date > '2026-03-31'
    ORDER BY due_date
''')
print("Order Number | Type | Status | Due Date")
print("-" * 60)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")

# 5. 今天的日期参考
print("\n" + "=" * 80)
print("参考信息:")
print("=" * 80)
print("今天日期: 2026-02-03")

conn.close()
