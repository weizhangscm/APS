# -*- coding: utf-8 -*-
"""
分析工序名称和资源的对应关系
"""
import sqlite3

conn = sqlite3.connect('aps.db')
c = conn.cursor()

print("=" * 80)
print("1. 查看所有工序名称")
print("=" * 80)

c.execute('''
    SELECT DISTINCT o.name, COUNT(*) as count
    FROM operations o
    GROUP BY o.name
    ORDER BY o.name
''')
print("工序名称 | 数量")
print("-" * 40)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]}")

print("\n" + "=" * 80)
print("2. 查看所有资源及其工作中心")
print("=" * 80)

c.execute('''
    SELECT r.id, r.name, wc.id, wc.name
    FROM resources r
    JOIN work_centers wc ON r.work_center_id = wc.id
    ORDER BY wc.id, r.id
''')
print("Res ID | Resource Name | WC ID | Work Center")
print("-" * 70)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")

print("\n" + "=" * 80)
print("3. 分析工序名称与工作中心的关系")
print("=" * 80)

c.execute('''
    SELECT DISTINCT o.name, ro.work_center_id, wc.name
    FROM operations o
    JOIN routing_operations ro ON o.routing_operation_id = ro.id
    JOIN work_centers wc ON ro.work_center_id = wc.id
    ORDER BY ro.work_center_id, o.name
''')
print("工序名称 | WC ID | 工作中心")
print("-" * 60)
for row in c.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]}")

print("\n" + "=" * 80)
print("4. 建议的工序名称到资源的映射")
print("=" * 80)

# 基于工序名称的关键字来匹配资源
mapping_suggestion = """
根据工序名称关键字匹配资源的建议：

钣金车间 (WC 2) 的工序：
  - 冲压下料 → 冲床-1 (ID 7)
  - 折弯成型 → 折弯机-1 (ID 8)
  - 焊接 → 钣金工位-1 (ID 9) 或 钣金工位-2 (ID 10)

其他工作中心 (取第一个资源):
  - 精密加工/装配配件/性能测试/检测/包装 等 → 对应工作中心的第一个资源
"""
print(mapping_suggestion)

conn.close()
