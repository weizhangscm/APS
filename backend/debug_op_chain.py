# -*- coding: utf-8 -*-
"""
调试工序链问题 - 为什么后续工序被排到很远
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

# 查看 PLN20260008 的工序链
print("=" * 80)
print("PLN20260008 的工序链（交货期: 2026-02-01）:")
print("=" * 80)
c.execute('''
    SELECT o.sequence, o.name, o.run_time, r.id, r.name,
           o.scheduled_start, o.scheduled_end
    FROM operations o
    JOIN resources r ON o.resource_id = r.id
    JOIN production_orders po ON o.order_id = po.id
    WHERE po.order_number = 'PLN20260008'
    ORDER BY o.sequence
''')
print("Seq | Op Name | Run Time | Res ID | Resource | Start | End")
print("-" * 100)
prev_end = None
for row in c.fetchall():
    gap = ""
    if prev_end and row[5]:
        from datetime import datetime
        start = datetime.strptime(row[5], '%Y-%m-%d %H:%M:%S.%f')
        end_prev = datetime.strptime(prev_end, '%Y-%m-%d %H:%M:%S.%f')
        gap_days = (start - end_prev).days
        gap = f" (gap: {gap_days} days)"
    print(f"{row[0]} | {row[1]} | {row[2]:.1f}h | {row[3]} | {row[4]} | {row[5]} | {row[6]}{gap}")
    prev_end = row[6]

print("\n" + "=" * 80)
print("PLN20260009 的工序链（交货期: 2026-02-01）:")
print("=" * 80)
c.execute('''
    SELECT o.sequence, o.name, o.run_time, r.id, r.name,
           o.scheduled_start, o.scheduled_end
    FROM operations o
    JOIN resources r ON o.resource_id = r.id
    JOIN production_orders po ON o.order_id = po.id
    WHERE po.order_number = 'PLN20260009'
    ORDER BY o.sequence
''')
print("Seq | Op Name | Run Time | Res ID | Resource | Start | End")
print("-" * 100)
prev_end = None
for row in c.fetchall():
    gap = ""
    if prev_end and row[5]:
        from datetime import datetime
        start = datetime.strptime(row[5], '%Y-%m-%d %H:%M:%S.%f')
        end_prev = datetime.strptime(prev_end, '%Y-%m-%d %H:%M:%S.%f')
        gap_days = (start - end_prev).days
        gap = f" (gap: {gap_days} days)"
    print(f"{row[0]} | {row[1]} | {row[2]:.1f}h | {row[3]} | {row[4]} | {row[5]} | {row[6]}{gap}")
    prev_end = row[6]

print("\n" + "=" * 80)
print("检查工序10、20的前序工序情况:")
print("=" * 80)
c.execute('''
    SELECT o.sequence, o.name, o.run_time, o.resource_id, o.status,
           o.scheduled_start, o.scheduled_end
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    WHERE po.order_number IN ('PLN20260008', 'PLN20260009', 'PLN20260033')
      AND o.sequence IN (10, 20)
    ORDER BY po.order_number, o.sequence
''')
print("Order | Seq | Op Name | Run Time | Res ID | Status | Start | End")
print("-" * 100)
for row in c.fetchall():
    print(f"? | {row[0]} | {row[1]} | {row[2]:.1f}h | {row[3]} | {row[4]} | {row[5]} | {row[6]}")

conn.close()
