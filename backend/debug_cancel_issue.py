# -*- coding: utf-8 -*-
"""
调试取消计划问题
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

print("=" * 80)
print("1. 检查截图中的订单类型")
print("=" * 80)

# 截图中显示的订单
orders_in_screenshot = [
    'PRD20260010',  # 20 折弯成型, 30 焊接
    'PLN20260008',  # 10 冲压下料, 30 焊接
    'PLN20260033',  # 20 折弯成型
    'PRD20260002',  # 10 冲压下料, 20 折弯成型, 30 焊接
]

c.execute('''
    SELECT order_number, order_type, status
    FROM production_orders
    WHERE order_number IN (?, ?, ?, ?)
''', orders_in_screenshot)

print("Order Number | Type | Status")
print("-" * 50)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]}")

print("\n" + "=" * 80)
print("2. 检查这些订单的工序状态")
print("=" * 80)

c.execute('''
    SELECT po.order_number, po.order_type, o.sequence, o.name, o.status, 
           o.scheduled_start, o.resource_id
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    WHERE po.order_number IN (?, ?, ?, ?)
    ORDER BY po.order_number, o.sequence
''', orders_in_screenshot)

print("Order | Type | Seq | Name | Status | Start | Resource")
print("-" * 100)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]}")

print("\n" + "=" * 80)
print("3. 检查取消计划的过滤条件")
print("=" * 80)

# 检查后端 cancel_plan 的逻辑
print("""
取消计划的条件 (根据代码):
1. 只取消 order_type = 'planned' 的订单 (计划订单)
2. 不取消 order_type = 'production' 的订单 (生产订单)
3. 根据选择的 resource_ids 和 product_ids 过滤
""")

# 检查 PRD 开头的订单
c.execute('''
    SELECT order_number, order_type, status
    FROM production_orders
    WHERE order_number LIKE 'PRD%'
    LIMIT 10
''')
print("\nPRD开头的订单 (生产订单):")
print("Order Number | Type | Status")
print("-" * 50)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]}")

conn.close()

print("\n" + "=" * 80)
print("结论:")
print("=" * 80)
print("""
PRD20260010 和 PRD20260002 是 'production' 类型的生产订单，
而取消计划功能只取消 'planned' 类型的计划订单。

这是设计上的预期行为：
- 生产订单 (PRD) = 已确认的订单，不应该被取消计划自动取消
- 计划订单 (PLN) = 待确认的订单，可以被取消计划
""")
