# -*- coding: utf-8 -*-
"""
根据工序名称匹配正确的资源 (完整版)

查看所有工序名称和对应资源:
- CNC精加工, CNC粗加工 → CNC车床-1 (ID 1)
- 冲压下料 → 冲床-1 (ID 7)
- 性能测试 → 检测设备-1 (ID 17)
- 包装 → 包装线-1 (ID 20)
- 喷涂 → 喷涂线-1 (ID 15)
- 折弯成型 → 折弯机-1 (ID 8)
- 检测 → 检测设备-1 (ID 17)
- 焊接 → 钣金工位-1 (ID 9)
- 精密加工 → 车床-1 (ID 4)
- 性能检测 → 检测设备-1 (ID 17)
- 组装 → 装配工位-1 (ID 11)
- 装配配件 → 装配工位-1 (ID 11)
- 装配 → 装配工位-1 (ID 11)
- 车削加工 → CNC车床-1 (ID 1) 或 车床-1 (ID 4)
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

# 定义工序名称到资源ID的完整映射
OPERATION_NAME_TO_RESOURCE = {
    # 钣金车间 (WC 2)
    '冲压下料': 7,      # 冲床-1
    '折弯成型': 8,      # 折弯机-1
    '焊接': 9,          # 钣金工位-1
    
    # 机加工车间 (WC 1)
    'CNC精加工': 1,     # CNC车床-1
    'CNC粗加工': 1,     # CNC车床-1
    '精密加工': 4,      # 车床-1
    '车削加工': 1,      # CNC车床-1 (车削类工序用CNC)
    
    # 装配车间 (WC 3)
    '组件': 11,         # 装配工位-1
    '组装': 11,         # 装配工位-1
    '装配配件': 11,     # 装配工位-1
    '装配': 11,         # 装配工位-1
    
    # 喷涂车间 (WC 4)
    '喷涂': 15,         # 喷涂线-1
    
    # 检测车间 (WC 5)
    '检测': 17,         # 检测设备-1
    '性能测试': 17,     # 检测设备-1
    '性能检测': 17,     # 检测设备-1
    
    # 包装车间 (WC 6)
    '包装': 20,         # 包装线-1
}

print("=" * 80)
print("根据工序名称匹配资源 (完整版)")
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
    # 根据工序名称查找正确的资源ID
    correct_resource_id = OPERATION_NAME_TO_RESOURCE.get(op_name)
    
    if correct_resource_id and correct_resource_id != current_resource_id:
        # 更新资源ID
        c.execute('UPDATE operations SET resource_id = ? WHERE id = ?', (correct_resource_id, op_id))
        
        old_name = resource_names.get(current_resource_id, 'None')
        new_name = resource_names.get(correct_resource_id, 'Unknown')
        print(f"  {order_number} - {op_name}: {old_name} -> {new_name}")
        updated_count += 1

conn.commit()

print(f"\n已更新 {updated_count} 个工序的资源分配")

# 验证结果 - 显示几个订单的工序
print("\n" + "=" * 80)
print("验证样例订单")
print("=" * 80)

for order_num in ['PRD20260010', 'PLN20260002', 'PLN20260027']:
    print(f"\n{order_num}:")
    c.execute('''
        SELECT o.sequence, o.name, r.name as resource_name
        FROM operations o
        LEFT JOIN resources r ON o.resource_id = r.id
        JOIN production_orders po ON o.order_id = po.id
        WHERE po.order_number = ?
        ORDER BY o.sequence
    ''', (order_num,))
    
    for row in c.fetchall():
        print(f"  {row[0]} {row[1]} -> {row[2]}")

conn.close()
print("\n完成！")
