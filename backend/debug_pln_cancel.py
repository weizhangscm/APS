# -*- coding: utf-8 -*-
"""
调试为什么 PLN20260008 和 PLN20260033 没有被取消
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

print("=" * 80)
print("1. 检查 PLN20260008 和 PLN20260033 的工序详情")
print("=" * 80)

c.execute('''
    SELECT po.order_number, po.product_id, p.name as product_name,
           o.sequence, o.name, o.status, o.resource_id, r.name as resource_name,
           o.scheduled_start
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    JOIN products p ON po.product_id = p.id
    LEFT JOIN resources r ON o.resource_id = r.id
    WHERE po.order_number IN ('PLN20260008', 'PLN20260033')
    ORDER BY po.order_number, o.sequence
''')

print("Order | Product | Seq | Op Name | Status | Res ID | Resource | Start")
print("-" * 110)
for row in c.fetchall():
    print(f"{row[0]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]} | {row[7]} | {row[8]}")

print("\n" + "=" * 80)
print("2. 检查筛选条件 - 冲床-1 的资源ID")
print("=" * 80)

c.execute("SELECT id, name, work_center_id FROM resources WHERE name LIKE '%冲床%' OR id = 7")
print("Resource ID | Name | WC ID")
print("-" * 40)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]}")

print("\n" + "=" * 80)
print("3. 检查 PLN20260008 和 PLN20260033 的工序是否在冲床-1上")
print("=" * 80)

c.execute('''
    SELECT po.order_number, o.sequence, o.name, o.resource_id, r.name
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    LEFT JOIN resources r ON o.resource_id = r.id
    WHERE po.order_number IN ('PLN20260008', 'PLN20260033')
      AND o.resource_id = 7
''')
rows = c.fetchall()
if rows:
    print("Order | Seq | Op Name | Res ID | Resource")
    print("-" * 60)
    for row in rows:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")
else:
    print("没有找到在冲床-1 (resource_id=7) 上的工序！")

print("\n" + "=" * 80)
print("4. 检查这两个订单的产品")
print("=" * 80)

c.execute('''
    SELECT order_number, product_id, p.name
    FROM production_orders po
    JOIN products p ON po.product_id = p.id
    WHERE order_number IN ('PLN20260008', 'PLN20260033')
''')
print("Order | Product ID | Product Name")
print("-" * 50)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]}")

print("\n" + "=" * 80)
print("5. 检查截图中的筛选条件：精密齿轮+9 的产品ID")
print("=" * 80)

c.execute("SELECT id, name FROM products WHERE name LIKE '%精密齿轮%' OR name LIKE '%齿轮%'")
print("Product ID | Name")
print("-" * 40)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]}")

# 检查产品ID 1 是什么
c.execute("SELECT id, name FROM products ORDER BY id")
print("\n所有产品:")
print("Product ID | Name")
print("-" * 40)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]}")

conn.close()

print("\n" + "=" * 80)
print("结论分析:")
print("=" * 80)
print("""
取消计划需要同时满足:
1. 订单类型 = planned (计划订单)
2. 工序已排程 (scheduled_start IS NOT NULL)
3. 工序的 resource_id 在选中的资源列表中
4. 订单的 product_id 在选中的产品列表中

如果 PLN20260008/PLN20260033 的工序不在 "冲床-1" 资源上，
或者它们的产品不在 "精密齿轮+9" 的筛选中，
就不会被取消。
""")
