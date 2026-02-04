# -*- coding: utf-8 -*-
"""
验证所有订单工序的资源分配是否正确
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

# 期望的映射
EXPECTED = {
    '冲压下料': '冲床-1',
    '折弯成型': '折弯机-1',
    '焊接': '钣金工位-1',
    'CNC精加工': 'CNC车床-1',
    'CNC粗加工': 'CNC车床-1',
    '精密加工': '车床-1',
    '车削加工': '车床-1',
    '组件': '装配工位-1',
    '装配配件': '装配工位-1',
    '装配': '装配工位-1',
    '喷涂': '喷涂线-1',
    '检测': '检测设备-1',
    '性能测试': '检测设备-1',
    '性能检测': '检测设备-1',
    '包装': '包装线-1',
}

print("=" * 80)
print("验证工序资源分配")
print("=" * 80)

c.execute('''
    SELECT o.name as op_name, r.name as resource_name, COUNT(*) as count
    FROM operations o
    LEFT JOIN resources r ON o.resource_id = r.id
    GROUP BY o.name, r.name
    ORDER BY o.name
''')

print("工序名称 | 当前资源 | 数量 | 状态")
print("-" * 70)

all_correct = True
for row in c.fetchall():
    op_name = row[0]
    resource_name = row[1]
    count = row[2]
    
    expected_resource = EXPECTED.get(op_name)
    if expected_resource:
        status = "OK" if resource_name == expected_resource else f"应为 {expected_resource}"
        if resource_name != expected_resource:
            all_correct = False
    else:
        status = "无映射规则"
    
    print(f"{op_name} | {resource_name} | {count} | {status}")

print()
if all_correct:
    print("所有工序资源分配正确!")
else:
    print("存在错误分配，请检查上方标记")

conn.close()
