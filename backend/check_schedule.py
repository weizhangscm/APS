"""
查询数据库中的最新排程数据
"""
import sqlite3
import os
from datetime import datetime

db_path = r'c:\Users\Chun.Wang\Desktop\APS\backend\aps.db'

if not os.path.exists(db_path):
    print(f"Database not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查看表结构
print("=" * 60)
print("数据库表:")
print("=" * 60)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for t in tables:
    print(f"  - {t[0]}")

# 查询资源
print("\n" + "=" * 60)
print("资源列表:")
print("=" * 60)
try:
    cursor.execute("SELECT id, name, capacity_per_day FROM resources ORDER BY id")
    resources = cursor.fetchall()
    for r in resources:
        print(f"  ID:{r[0]} | {r[1]} | 产能:{r[2]}H/天")
except Exception as e:
    print(f"  Error: {e}")

# 查询产品
print("\n" + "=" * 60)
print("产品列表:")
print("=" * 60)
try:
    cursor.execute("SELECT id, name, product_number FROM products ORDER BY id")
    products = cursor.fetchall()
    for p in products:
        print(f"  ID:{p[0]} | {p[2]} - {p[1]}")
except Exception as e:
    print(f"  Error: {e}")

# 查询订单及其排程状态
print("\n" + "=" * 60)
print("订单排程状态:")
print("=" * 60)
try:
    cursor.execute("""
        SELECT o.id, o.order_number, o.order_type, o.status, o.due_date, p.name as product_name
        FROM production_orders o
        LEFT JOIN products p ON o.product_id = p.id
        ORDER BY o.due_date
    """)
    orders = cursor.fetchall()
    for order in orders:
        print(f"  {order[1]} | 类型:{order[2]} | 状态:{order[3]} | 交期:{order[4]} | 产品:{order[5]}")
except Exception as e:
    print(f"  Error: {e}")

# 查询已排程的工序
print("\n" + "=" * 60)
print("已排程的工序 (按资源分组):")
print("=" * 60)
try:
    cursor.execute("""
        SELECT 
            r.name as resource_name,
            o.order_number,
            op.name as op_name,
            op.sequence,
            op.scheduled_start,
            op.scheduled_end,
            op.status,
            p.name as product_name
        FROM operations op
        LEFT JOIN resources r ON op.resource_id = r.id
        LEFT JOIN production_orders o ON op.order_id = o.id
        LEFT JOIN products p ON o.product_id = p.id
        WHERE op.scheduled_start IS NOT NULL
        ORDER BY r.name, op.scheduled_start
    """)
    operations = cursor.fetchall()
    
    current_resource = None
    total_hours_by_resource = {}
    
    for op in operations:
        resource_name = op[0] or "未分配"
        if resource_name != current_resource:
            if current_resource:
                print(f"    --- 小计: {total_hours_by_resource.get(current_resource, 0):.1f}H ---")
            current_resource = resource_name
            print(f"\n  【{resource_name}】")
            total_hours_by_resource[resource_name] = 0
        
        # 计算工时
        if op[4] and op[5]:
            start = datetime.fromisoformat(op[4].replace('Z', '+00:00').replace('+00:00', ''))
            end = datetime.fromisoformat(op[5].replace('Z', '+00:00').replace('+00:00', ''))
            hours = (end - start).total_seconds() / 3600
            total_hours_by_resource[resource_name] = total_hours_by_resource.get(resource_name, 0) + hours
        else:
            hours = 0
        
        print(f"    {op[1]} | 工序{op[3]}:{op[2]} | {op[4][:16] if op[4] else '-'} ~ {op[5][:16] if op[5] else '-'} | {hours:.1f}H | 产品:{op[7]}")
    
    if current_resource:
        print(f"    --- 小计: {total_hours_by_resource.get(current_resource, 0):.1f}H ---")
    
    print(f"\n  总计: {len(operations)} 个已排程工序")

except Exception as e:
    print(f"  Error: {e}")
    import traceback
    traceback.print_exc()

# 统计按产品的排程情况
print("\n" + "=" * 60)
print("按产品统计排程情况:")
print("=" * 60)
try:
    cursor.execute("""
        SELECT 
            p.name as product_name,
            COUNT(DISTINCT o.id) as order_count,
            COUNT(op.id) as op_count,
            MIN(op.scheduled_start) as earliest_start,
            MAX(op.scheduled_end) as latest_end
        FROM products p
        LEFT JOIN production_orders o ON p.id = o.product_id
        LEFT JOIN operations op ON o.id = op.order_id AND op.scheduled_start IS NOT NULL
        GROUP BY p.id, p.name
        HAVING op_count > 0
        ORDER BY earliest_start
    """)
    product_stats = cursor.fetchall()
    
    for ps in product_stats:
        if ps[3] and ps[4]:
            start = datetime.fromisoformat(ps[3].replace('Z', '+00:00').replace('+00:00', ''))
            end = datetime.fromisoformat(ps[4].replace('Z', '+00:00').replace('+00:00', ''))
            span_hours = (end - start).total_seconds() / 3600
        else:
            span_hours = 0
        print(f"  {ps[0]} | {ps[1]}订单 | {ps[2]}工序 | 跨度:{span_hours:.1f}H | {ps[3][:10] if ps[3] else '-'} ~ {ps[4][:10] if ps[4] else '-'}")

except Exception as e:
    print(f"  Error: {e}")
    import traceback
    traceback.print_exc()

conn.close()
print("\n" + "=" * 60)
print("查询完成")
