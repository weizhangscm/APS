# -*- coding: utf-8 -*-
"""
清除交货期从2026-02-09以后的计划订单的排程
"""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('aps.db')
c = conn.cursor()

# 交货期起始日期
cutoff_date = '2026-02-09 00:00:00'

print("=" * 80)
print(f"清除交货期 >= {cutoff_date} 的计划订单排程")
print("=" * 80)

# 查找符合条件的计划订单
c.execute('''
    SELECT id, order_number, due_date, status
    FROM production_orders
    WHERE order_type = 'planned'
      AND due_date >= ?
    ORDER BY due_date
''', (cutoff_date,))

orders = c.fetchall()
print(f"找到 {len(orders)} 个符合条件的计划订单:\n")

for order in orders:
    order_id, order_number, due_date, status = order
    print(f"  {order_number}: 交货期={due_date[:10]}, 当前状态={status}")

# 确认后执行清除
print("\n" + "=" * 80)
print("开始清除排程...")
print("=" * 80)

cleared_orders = 0
cleared_ops = 0

for order in orders:
    order_id, order_number, due_date, status = order
    
    # 更新订单状态为 created（待排程）
    c.execute('''
        UPDATE production_orders
        SET status = 'created'
        WHERE id = ?
    ''', (order_id,))
    
    # 更新该订单的所有工序状态为 pending，清除排程时间
    c.execute('''
        UPDATE operations
        SET status = 'pending',
            scheduled_start = NULL,
            scheduled_end = NULL,
            changeover_time = 0
        WHERE order_id = ?
    ''', (order_id,))
    
    ops_updated = c.rowcount
    cleared_orders += 1
    cleared_ops += ops_updated
    
    print(f"  清除 {order_number}: 订单状态->created, {ops_updated}个工序状态->pending")

conn.commit()

print(f"\n完成！共清除 {cleared_orders} 个订单, {cleared_ops} 个工序的排程")

# 验证结果
print("\n" + "=" * 80)
print("验证结果")
print("=" * 80)

c.execute('''
    SELECT order_number, status, 
           (SELECT COUNT(*) FROM operations o WHERE o.order_id = po.id AND o.status = 'pending') as pending_ops,
           (SELECT COUNT(*) FROM operations o WHERE o.order_id = po.id) as total_ops
    FROM production_orders po
    WHERE order_type = 'planned'
      AND due_date >= ?
    ORDER BY due_date
    LIMIT 10
''', (cutoff_date,))

print("前10个订单:")
for row in c.fetchall():
    print(f"  {row[0]}: 状态={row[1]}, 待排程工序={row[2]}/{row[3]}")

conn.close()
