# -*- coding: utf-8 -*-
"""
直接测试过滤逻辑（不通过API）
"""
import sys
sys.path.insert(0, '.')

from datetime import datetime
from app.database import SessionLocal
from app import models

db = SessionLocal()

# 模拟显示区间
display_start = datetime(2026, 2, 4, 0, 0, 0)
display_end = datetime(2026, 2, 15, 23, 59, 59)

print("="*80)
print("测试显示区间过滤逻辑")
print("="*80)
print(f"显示区间: {display_start} ~ {display_end}")
print("="*80)

# 获取 CNC机床-3 上的所有工序
target_operations = db.query(models.Operation).filter(
    models.Operation.resource_id == 3
).all()

print(f"\n过滤前: CNC机床-3 上共有 {len(target_operations)} 个工序")

# 模拟过滤逻辑
filtered_operations = []
for op in target_operations:
    order = db.query(models.ProductionOrder).filter(
        models.ProductionOrder.id == op.order_id
    ).first()
    
    if order:
        # 检查交货期是否在显示区间内
        due_date_in_range = (
            order.due_date and 
            display_start <= order.due_date <= display_end
        )
        # 检查排程时间是否在显示区间内
        scheduled_in_range = (
            op.scheduled_start and op.scheduled_end and
            op.scheduled_start <= display_end and op.scheduled_end >= display_start
        )
        
        if due_date_in_range or scheduled_in_range:
            filtered_operations.append(op)
            print(f"  [包含] 订单 {order.order_number}, 交货期: {order.due_date.strftime('%Y-%m-%d') if order.due_date else 'None'}")
        else:
            print(f"  [排除] 订单 {order.order_number}, 交货期: {order.due_date.strftime('%Y-%m-%d') if order.due_date else 'None'} (超出显示区间)")

print(f"\n过滤后: 剩余 {len(filtered_operations)} 个工序")
print("\n应该只排程以下订单:")
order_numbers = list(set([
    db.query(models.ProductionOrder).filter(models.ProductionOrder.id == op.order_id).first().order_number
    for op in filtered_operations
]))
for on in sorted(order_numbers):
    print(f"  - {on}")

db.close()
