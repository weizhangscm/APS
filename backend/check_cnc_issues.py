# -*- coding: utf-8 -*-
import sqlite3
conn = sqlite3.connect('aps.db')
cursor = conn.cursor()

print('=' * 80)
print('问题1: 检查 CNC机床-3 (resource_id=3) 上的工序详情')
print('=' * 80)

cursor.execute("""
    SELECT po.order_number, po.due_date, po.status as order_status,
           o.name, o.sequence, o.run_time, o.setup_time,
           o.scheduled_start, o.scheduled_end, o.status as op_status, 
           o.resource_id
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    WHERE o.resource_id = 3
    ORDER BY po.due_date
""")
results = cursor.fetchall()
print(f'CNC机床-3 共有 {len(results)} 个工序:')
print()
for r in results:
    print(f'订单: {r[0]}')
    print(f'  交货期: {r[1]}, 订单状态: {r[2]}')
    print(f'  工序: {r[3]}, 序号: {r[4]}, 运行时间: {r[5]}分钟, 设置时间: {r[6]}分钟')
    print(f'  排程: {r[7]} ~ {r[8]}, 状态: {r[9]}')
    print(f'  resource_id: {r[10]}')
    print()

print('=' * 80)
print('问题2: 检查 PLN20260035 订单的所有工序')
print('=' * 80)

cursor.execute("""
    SELECT po.order_number, po.due_date, po.status as order_status,
           o.name, o.sequence, o.run_time, o.setup_time,
           o.scheduled_start, o.scheduled_end, o.status as op_status, 
           o.resource_id
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    WHERE po.order_number = 'PLN20260035'
    ORDER BY o.sequence
""")
results = cursor.fetchall()
print(f'PLN20260035 共有 {len(results)} 个工序:')
print()
for r in results:
    print(f'  序号 {r[4]}: {r[3]}')
    print(f'    运行时间: {r[5]}分钟, 设置时间: {r[6]}分钟')
    print(f'    排程: {r[7]} ~ {r[8]}, 状态: {r[9]}')
    print(f'    resource_id: {r[10]}')
    print()

# 检查 resource_id=1,3 对应哪个资源
cursor.execute("SELECT id, name FROM resources WHERE id IN (1, 3)")
resources = cursor.fetchall()
print('资源映射:')
for r in resources:
    print(f'  resource_id={r[0]}: {r[1]}')

print()
print('=' * 80)
print('检查 CNC工作中心 下有哪些资源')
print('=' * 80)
cursor.execute("""
    SELECT r.id, r.name, wc.name as wc_name
    FROM resources r
    JOIN work_centers wc ON r.work_center_id = wc.id
    WHERE wc.name LIKE '%CNC%'
    ORDER BY r.id
""")
results = cursor.fetchall()
for r in results:
    print(f'  resource_id={r[0]}: {r[1]} (工作中心: {r[2]})')

print()
print('=' * 80)
print('检查 PLN20260035 的10工序 resource_id')
print('=' * 80)
cursor.execute("""
    SELECT po.order_number, o.sequence, o.name, o.resource_id, r.name as resource_name
    FROM operations o
    JOIN production_orders po ON o.order_id = po.id
    LEFT JOIN resources r ON o.resource_id = r.id
    WHERE po.order_number = 'PLN20260035' AND o.sequence = 10
""")
results = cursor.fetchall()
for r in results:
    print(f'订单: {r[0]}, 序号: {r[1]}, 工序: {r[2]}')
    print(f'  resource_id: {r[3]}, 资源名称: {r[4]}')

conn.close()
