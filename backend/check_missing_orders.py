# -*- coding: utf-8 -*-
"""
检查为什么 PLN20260011 和 PLN20260005 没有显示在资源视图中
"""
import sys
sys.path.insert(0, '.')

from datetime import datetime
from app.database import SessionLocal
from app import models

db = SessionLocal()

print("="*80)
print("检查 PLN20260011 和 PLN20260005 为什么没有显示")
print("="*80)

# 检查这两个订单
order_numbers = ['PLN20260011', 'PLN20260005']

for order_number in order_numbers:
    print(f"\n{'='*40}")
    print(f"订单: {order_number}")
    print(f"{'='*40}")
    
    order = db.query(models.ProductionOrder).filter(
        models.ProductionOrder.order_number == order_number
    ).first()
    
    if order:
        print(f"  订单ID: {order.id}")
        print(f"  订单类型: {order.order_type}")
        print(f"  订单状态: {order.status}")
        print(f"  交货期: {order.due_date}")
        print(f"  产品ID: {order.product_id}")
        
        # 检查工序
        ops = db.query(models.Operation).filter(
            models.Operation.order_id == order.id
        ).all()
        
        print(f"\n  工序数量: {len(ops)}")
        for op in ops:
            print(f"\n  工序: {op.name} (ID={op.id})")
            print(f"    资源ID: {op.resource_id}")
            print(f"    排程开始: {op.scheduled_start}")
            print(f"    排程结束: {op.scheduled_end}")
            print(f"    状态: {op.status}")
            
            # 检查资源是否是 CNC机床-3
            if op.resource_id:
                resource = db.query(models.Resource).filter(
                    models.Resource.id == op.resource_id
                ).first()
                if resource:
                    print(f"    资源名称: {resource.name}")
    else:
        print(f"  订单不存在!")

# 检查 CNC机床-3 上有哪些订单
print(f"\n{'='*80}")
print("CNC机床-3 (ID=3) 上的所有工序:")
print("="*80)

ops_on_cnc3 = db.query(models.Operation).filter(
    models.Operation.resource_id == 3
).all()

print(f"总共 {len(ops_on_cnc3)} 个工序")
for op in ops_on_cnc3:
    order = db.query(models.ProductionOrder).filter(
        models.ProductionOrder.id == op.order_id
    ).first()
    order_number = order.order_number if order else "Unknown"
    order_due_date = order.due_date if order else "Unknown"
    
    print(f"\n  订单: {order_number}")
    print(f"    工序: {op.name} (ID={op.id})")
    print(f"    排程开始: {op.scheduled_start}")
    print(f"    排程结束: {op.scheduled_end}")
    print(f"    订单交货期: {order_due_date}")
    print(f"    工序状态: {op.status}")

db.close()
