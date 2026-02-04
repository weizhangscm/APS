# -*- coding: utf-8 -*-
"""
调试排程问题：模拟排程算法对 PLN20260014 的处理过程
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

print("=" * 80)
print("模拟排程算法处理 PLN20260014")
print("=" * 80)

# 获取订单
c.execute('''
    SELECT id, order_number, product_id FROM production_orders 
    WHERE order_number = 'PLN20260014'
''')
order = c.fetchone()
order_id, order_number, product_id = order

print(f"订单: {order_number}, product_id: {product_id}")

# 获取工序
c.execute('''
    SELECT o.id, o.sequence, o.name, o.routing_operation_id, o.run_time
    FROM operations o
    WHERE o.order_id = ?
    ORDER BY o.sequence
''', (order_id,))

operations = c.fetchall()

print(f"\n工序列表 ({len(operations)}个):")
for op in operations:
    op_id, seq, name, routing_op_id, run_time = op
    
    # 获取 routing_operation 的 work_center_id
    c.execute('''
        SELECT work_center_id FROM routing_operations WHERE id = ?
    ''', (routing_op_id,))
    ro = c.fetchone()
    work_center_id = ro[0] if ro else None
    
    # 获取该工作中心的可用资源
    c.execute('''
        SELECT id, name FROM resources WHERE work_center_id = ?
    ''', (work_center_id,))
    resources = c.fetchall()
    
    print(f"\n  {seq} {name}:")
    print(f"    routing_operation_id: {routing_op_id}")
    print(f"    work_center_id: {work_center_id}")
    print(f"    run_time: {run_time}h")
    print(f"    可用资源: {resources}")
    
    if not resources:
        print(f"    ⚠️ 没有可用资源！这个工序会被跳过")

conn.close()
