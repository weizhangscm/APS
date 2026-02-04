# -*- coding: utf-8 -*-
"""
恢复原有资源分配

只修改以下工序（根据工序名称匹配特定资源）：
- 钣金车间的工序：冲压下料→冲床-1, 折弯成型→折弯机-1, 焊接→焊接工位-1
- 其他工序保持原有分配，不统一改为-1
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

# 只有这些工序需要根据名称强制匹配特定资源
# 其他工序保持工作中心内的原有资源分配
FORCE_MAPPING = {
    # 钣金车间的工序必须匹配正确的资源类型
    '冲压下料': 7,      # 冲床-1
    '折弯成型': 8,      # 折弯机-1
    '焊接': 9,          # 焊接工位-1
}

print("=" * 80)
print("只修复钣金车间工序的资源分配")
print("=" * 80)

# 获取资源名称映射
c.execute('SELECT id, name FROM resources')
resource_names = {row[0]: row[1] for row in c.fetchall()}

# 只修复需要强制映射的工序
for op_name, correct_resource_id in FORCE_MAPPING.items():
    c.execute('''
        SELECT o.id, o.resource_id, po.order_number
        FROM operations o
        JOIN production_orders po ON o.order_id = po.id
        WHERE o.name = ? AND o.resource_id != ?
    ''', (op_name, correct_resource_id))
    
    for row in c.fetchall():
        op_id, current_resource_id, order_number = row
        c.execute('UPDATE operations SET resource_id = ? WHERE id = ?', (correct_resource_id, op_id))
        old_name = resource_names.get(current_resource_id, 'None')
        new_name = resource_names.get(correct_resource_id, 'Unknown')
        print(f"  {order_number} - {op_name}: {old_name} -> {new_name}")

conn.commit()

# 显示当前状态
print("\n" + "=" * 80)
print("当前工序资源分配汇总")
print("=" * 80)

c.execute('''
    SELECT o.name as op_name, r.name as resource_name, COUNT(*) as count
    FROM operations o
    LEFT JOIN resources r ON o.resource_id = r.id
    GROUP BY o.name, r.name
    ORDER BY o.name, r.name
''')

print("{:<15} | {:<15} | {:>5}".format("工序名称", "资源", "数量"))
print("-" * 45)
for row in c.fetchall():
    print("{:<15} | {:<15} | {:>5}".format(
        row[0] if row[0] else 'NULL', 
        row[1] if row[1] else 'NULL', 
        row[2]
    ))

conn.close()
print("\n完成！")
