# -*- coding: utf-8 -*-
"""
详细调试取消计划问题
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

print("=" * 80)
print("筛选条件分析：")
print("  资源: 冲床-1 (resource_id = 7)")
print("  产品: 精密齿轮 +9 = 所有10个产品都被选中")
print("=" * 80)

print("\n1. PLN20260008 和 PLN20260033 在冲床-1上有工序吗？")
print("-" * 80)

c.execute('''
    SELECT po.order_number, o.sequence, o.name, o.resource_id, r.name, o.status, o.scheduled_start
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    LEFT JOIN resources r ON o.resource_id = r.id
    WHERE po.order_number IN ('PLN20260008', 'PLN20260033')
    ORDER BY po.order_number, o.sequence
''')

print("Order | Seq | Op Name | Res ID | Resource | Status | Start")
print("-" * 100)
for row in c.fetchall():
    marker = " <-- 冲床-1" if row[3] == 7 else ""
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]}{marker}")

print("\n2. 哪些工序在冲床-1 (resource_id=7) 上且已排程？")
print("-" * 80)

c.execute('''
    SELECT po.order_number, po.order_type, o.sequence, o.name, o.status, o.scheduled_start
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    WHERE o.resource_id = 7
      AND o.scheduled_start IS NOT NULL
    ORDER BY o.scheduled_start
''')

rows = c.fetchall()
if rows:
    print("Order | Type | Seq | Op Name | Status | Start")
    print("-" * 80)
    for row in rows:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")
else:
    print(">>> 没有任何已排程的工序在冲床-1上！ <<<")

print("\n3. 冲床-1上有哪些工序（包括未排程的）？")
print("-" * 80)

c.execute('''
    SELECT po.order_number, po.order_type, o.sequence, o.name, o.status, o.scheduled_start
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    WHERE o.resource_id = 7
    ORDER BY po.order_number, o.sequence
''')

rows = c.fetchall()
if rows:
    print("Order | Type | Seq | Op Name | Status | Start")
    print("-" * 80)
    for row in rows:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")
else:
    print(">>> 冲床-1上没有分配任何工序！ <<<")

print("\n4. 检查甘特图显示的逻辑 - 截图中显示在冲床-1下的工序")
print("-" * 80)
print("""
截图显示的工序：
- PRD20260010 - 20 折弯成型
- PRD20260010 - 30 焊接
- PLN20260008 - 10 冲压下料
- PLN20260008 - 30 焊接
- PLN20260033 - 20 折弯成型
- PRD20260002 - 10 冲压下料
- PRD20260002 - 20 折弯成型
- PRD20260002 - 30 焊接

这些工序的实际 resource_id 是什么？
""")

orders_to_check = ['PRD20260010', 'PLN20260008', 'PLN20260033', 'PRD20260002']
sequences_to_check = [(10,), (20,), (30,)]

c.execute('''
    SELECT po.order_number, o.sequence, o.name, o.resource_id, r.name
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    LEFT JOIN resources r ON o.resource_id = r.id
    WHERE po.order_number IN (?, ?, ?, ?)
      AND o.sequence IN (10, 20, 30)
    ORDER BY po.order_number, o.sequence
''', orders_to_check)

print("Order | Seq | Op Name | Res ID | Resource")
print("-" * 70)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")

conn.close()

print("\n" + "=" * 80)
print("结论：")
print("=" * 80)
print("""
如果这些工序的 resource_id 不是 7 (冲床-1)，
说明它们被显示在冲床-1下是因为"兜底逻辑"：
  - 工序没有明确的 resource_id，通过工作中心匹配到冲床-1所在的工作中心
  - 但取消计划是按 resource_id 精确匹配的

这就造成了显示和取消逻辑不一致的问题！
""")
