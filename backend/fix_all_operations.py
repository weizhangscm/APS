# -*- coding: utf-8 -*-
"""
根据工序名称匹配正确的资源 - 完整版

映射规则：
钣金车间:
  - 冲压下料 → 冲床-1 (ID 7)
  - 折弯成型 → 折弯机-1 (ID 8)
  - 焊接 → 焊接工位-1 (ID 9)

机加工车间:
  - CNC精加工, CNC粗加工 → CNC机床-1 (ID 1)
  - 精密加工 → 车床-1 (ID 4)
  - 车削加工, 零件加工 → CNC机床-1 (ID 1)

装配车间:
  - 组件, 组装, 装配配件, 装配, 组装焊接 → 装配工位-1 (ID 11)

喷涂车间:
  - 喷涂 → 喷涂线-1 (ID 15)

检测车间:
  - 检测, 性能测试, 性能检测, 功能测试, 精密检测 → 检测设备-1 (ID 17)

包装车间:
  - 包装 → 包装线-1 (ID 20)
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

# 完整的工序名称到资源ID的映射
OPERATION_NAME_TO_RESOURCE = {
    # 钣金车间 (WC 2)
    '冲压下料': 7,      # 冲床-1
    '折弯成型': 8,      # 折弯机-1
    '焊接': 9,          # 焊接工位-1
    
    # 机加工车间 (WC 1)
    'CNC精加工': 1,     # CNC机床-1
    'CNC粗加工': 1,     # CNC机床-1
    '精密加工': 4,      # 车床-1
    '车削加工': 1,      # CNC机床-1
    '零件加工': 1,      # CNC机床-1
    
    # 装配车间 (WC 3)
    '组件': 11,         # 装配工位-1
    '组装': 11,         # 装配工位-1
    '组装焊接': 11,     # 装配工位-1
    '装配配件': 11,     # 装配工位-1
    '装配': 11,         # 装配工位-1
    
    # 喷涂车间 (WC 4)
    '喷涂': 15,         # 喷涂线-1
    
    # 检测车间 (WC 5)
    '检测': 17,         # 检测设备-1
    '性能测试': 17,     # 检测设备-1
    '性能检测': 17,     # 检测设备-1
    '功能测试': 17,     # 检测设备-1
    '精密检测': 17,     # 检测设备-1
    
    # 包装车间 (WC 6)
    '包装': 20,         # 包装线-1
}

print("=" * 80)
print("根据工序名称匹配资源")
print("=" * 80)

# 获取资源名称映射
c.execute('SELECT id, name FROM resources')
resource_names = {row[0]: row[1] for row in c.fetchall()}

# 查询所有工序
c.execute('''
    SELECT o.id, o.name, o.resource_id, po.order_number
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    ORDER BY po.order_number, o.sequence
''')

operations = c.fetchall()

updated_count = 0
for op_id, op_name, current_resource_id, order_number in operations:
    correct_resource_id = OPERATION_NAME_TO_RESOURCE.get(op_name)
    
    if correct_resource_id and correct_resource_id != current_resource_id:
        c.execute('UPDATE operations SET resource_id = ? WHERE id = ?', (correct_resource_id, op_id))
        
        old_name = resource_names.get(current_resource_id, 'None')
        new_name = resource_names.get(correct_resource_id, 'Unknown')
        print(f"  {order_number} - {op_name}: {old_name} -> {new_name}")
        updated_count += 1

conn.commit()

print(f"\n已更新 {updated_count} 个工序的资源分配")

# 验证最终结果
print("\n" + "=" * 80)
print("最终结果汇总")
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
