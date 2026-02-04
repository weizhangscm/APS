# -*- coding: utf-8 -*-
"""
修复现有工序的 resource_id 字段
根据工艺路线工序的工作中心，为每个工序分配默认资源
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

# 1. 建立工作中心到第一个资源的映射
c.execute('SELECT id, work_center_id FROM resources ORDER BY id')
work_center_to_first_resource = {}
for row in c.fetchall():
    resource_id, work_center_id = row
    if work_center_id not in work_center_to_first_resource:
        work_center_to_first_resource[work_center_id] = resource_id

print("Work center to first resource mapping:")
for wc_id, res_id in work_center_to_first_resource.items():
    c.execute('SELECT name FROM work_centers WHERE id = ?', (wc_id,))
    wc_name = c.fetchone()[0]
    c.execute('SELECT name FROM resources WHERE id = ?', (res_id,))
    res_name = c.fetchone()[0]
    print(f"  WC {wc_id} ({wc_name}) -> Resource {res_id} ({res_name})")

# 2. 查询所有 resource_id 为空的工序
c.execute('''
    SELECT o.id, o.routing_operation_id, ro.work_center_id
    FROM operations o
    JOIN routing_operations ro ON o.routing_operation_id = ro.id
    WHERE o.resource_id IS NULL
''')
ops_to_update = c.fetchall()
print(f"\nFound {len(ops_to_update)} operations with NULL resource_id")

# 3. 更新这些工序的 resource_id
updated_count = 0
for op_id, routing_op_id, work_center_id in ops_to_update:
    default_resource_id = work_center_to_first_resource.get(work_center_id)
    if default_resource_id:
        c.execute('UPDATE operations SET resource_id = ? WHERE id = ?', (default_resource_id, op_id))
        updated_count += 1

conn.commit()
print(f"Updated {updated_count} operations with default resource_id")

# 4. 验证结果
c.execute('''
    SELECT o.status, COUNT(*), 
           SUM(CASE WHEN o.resource_id IS NOT NULL THEN 1 ELSE 0 END) as has_resource
    FROM operations o
    GROUP BY o.status
''')
print("\nOperations by status after fix:")
print("Status | Count | Has Resource")
print("-" * 40)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]}")

conn.close()
print("\nDone!")
