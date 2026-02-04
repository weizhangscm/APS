# -*- coding: utf-8 -*-
"""
查找订单状态与工序状态不一致的情况
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

print("=" * 80)
print("查找订单状态为 scheduled 但有工序状态为 pending 的订单")
print("=" * 80)

c.execute('''
    SELECT DISTINCT po.order_number, po.status, po.order_type
    FROM production_orders po
    JOIN operations o ON o.order_id = po.id
    WHERE po.status = 'scheduled' 
      AND o.status = 'pending'
    ORDER BY po.order_number
''')

inconsistent_orders = c.fetchall()

if inconsistent_orders:
    print(f"发现 {len(inconsistent_orders)} 个不一致的订单:\n")
    
    for order_num, order_status, order_type in inconsistent_orders:
        print(f"订单 {order_num} ({order_type}, {order_status}):")
        
        c.execute('''
            SELECT o.sequence, o.name, o.status, o.scheduled_start
            FROM operations o
            JOIN production_orders po ON o.order_id = po.id
            WHERE po.order_number = ?
            ORDER BY o.sequence
        ''', (order_num,))
        
        for op in c.fetchall():
            status_mark = "⚠️" if op[2] == 'pending' else "✓"
            print(f"  {status_mark} {op[0]} {op[1]}: {op[2]}, start={op[3][:16] if op[3] else '-'}")
        print()
else:
    print("没有发现不一致的订单")

print("=" * 80)
print("统计：工序状态为 pending 但有 scheduled_start 的工序")
print("=" * 80)

c.execute('''
    SELECT COUNT(*)
    FROM operations
    WHERE status = 'pending' AND scheduled_start IS NOT NULL
''')
count = c.fetchone()[0]
print(f"共有 {count} 个工序状态为 pending 但有排程时间")

print("\n" + "=" * 80)
print("统计：工序状态为 scheduled 但没有 scheduled_start 的工序")
print("=" * 80)

c.execute('''
    SELECT COUNT(*)
    FROM operations
    WHERE status = 'scheduled' AND scheduled_start IS NULL
''')
count = c.fetchone()[0]
print(f"共有 {count} 个工序状态为 scheduled 但没有排程时间")

conn.close()
