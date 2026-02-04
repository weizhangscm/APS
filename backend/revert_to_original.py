# -*- coding: utf-8 -*-
"""
恢复之前被错误修改的资源分配

根据截图，需要恢复的工序：
- PLN20260004 - 零件加工: CNC机床-3 (不是CNC机床-1)
- PLN20260004 - 功能测试: 检测设备-2 (不是检测设备-1)
- PLN20260005 - 零件加工: CNC机床-3
- PLN20260005 - 组装焊接: 装配工位-3
- PLN20260005 - 功能测试: 检测设备-2
...等等
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

# 被修改的工序列表（需要恢复）
# 格式: (订单号, 工序名称, 原始资源ID)
REVERT_LIST = [
    # PLN20260004
    ('PLN20260004', '零件加工', 3),      # CNC机床-3
    ('PLN20260004', '功能测试', 18),     # 检测设备-2
    
    # PLN20260005
    ('PLN20260005', '零件加工', 3),      # CNC机床-3
    ('PLN20260005', '组装焊接', 13),     # 装配工位-3
    ('PLN20260005', '功能测试', 18),     # 检测设备-2
    
    # PLN20260010
    ('PLN20260010', '精密检测', 19),     # 检测设备-3
    
    # PLN20260011
    ('PLN20260011', '零件加工', 3),      # CNC机床-3
    
    # PLN20260015
    ('PLN20260015', '零件加工', 2),      # CNC机床-2
    ('PLN20260015', '组装焊接', 12),     # 装配工位-2
    ('PLN20260015', '功能测试', 19),     # 检测设备-3
    
    # PLN20260016
    ('PLN20260016', '零件加工', 3),      # CNC机床-3
    ('PLN20260016', '组装焊接', 12),     # 装配工位-2
    
    # PLN20260018
    ('PLN20260018', '零件加工', 5),      # 车床-2
    ('PLN20260018', '组装焊接', 13),     # 装配工位-3
    
    # PLN20260019
    ('PLN20260019', '精密检测', 19),     # 检测设备-3
    
    # PLN20260020
    ('PLN20260020', '零件加工', 6),      # 铣床-1
    ('PLN20260020', '组装焊接', 12),     # 装配工位-2
    ('PLN20260020', '功能测试', 19),     # 检测设备-3
    
    # PLN20260021
    ('PLN20260021', '精密检测', 18),     # 检测设备-2
    
    # PLN20260023
    ('PLN20260023', '精密检测', 18),     # 检测设备-2
    
    # PLN20260024
    ('PLN20260024', '精密检测', 19),     # 检测设备-3
    
    # PLN20260025
    ('PLN20260025', '精密检测', 19),     # 检测设备-3
    
    # PLN20260026
    ('PLN20260026', '精密检测', 19),     # 检测设备-3
    
    # PLN20260028
    ('PLN20260028', '精密检测', 19),     # 检测设备-3
    
    # PLN20260030
    ('PLN20260030', '零件加工', 3),      # CNC机床-3
    ('PLN20260030', '组装焊接', 14),     # 装配工位-4
    ('PLN20260030', '功能测试', 19),     # 检测设备-3
]

print("=" * 80)
print("恢复被错误修改的资源分配")
print("=" * 80)

# 获取资源名称映射
c.execute('SELECT id, name FROM resources')
resource_names = {row[0]: row[1] for row in c.fetchall()}

updated_count = 0
for order_number, op_name, original_resource_id in REVERT_LIST:
    # 查找工序
    c.execute('''
        SELECT o.id, o.resource_id
        FROM operations o
        JOIN production_orders po ON o.order_id = po.id
        WHERE po.order_number = ? AND o.name = ?
    ''', (order_number, op_name))
    
    result = c.fetchone()
    if result:
        op_id, current_resource_id = result
        if current_resource_id != original_resource_id:
            c.execute('UPDATE operations SET resource_id = ? WHERE id = ?', (original_resource_id, op_id))
            old_name = resource_names.get(current_resource_id, 'None')
            new_name = resource_names.get(original_resource_id, 'Unknown')
            print(f"  {order_number} - {op_name}: {old_name} -> {new_name}")
            updated_count += 1

conn.commit()
print(f"\n已恢复 {updated_count} 个工序的资源分配")

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
