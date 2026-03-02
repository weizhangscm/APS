# -*- coding: utf-8 -*-
"""
检查为什么排程不是从 2026-02-04 开始
"""
import sys
sys.path.insert(0, '.')

from datetime import datetime, timedelta
from app.database import SessionLocal
from app import models

db = SessionLocal()

print("="*80)
print("检查为什么排程不是从 2026-02-04 开始")
print("="*80)

# 1. 检查当前日期
now = datetime.now()
print(f"\n1. 当前系统时间: {now}")

# 2. 检查 CNC机床-3 的资源信息
resource = db.query(models.Resource).filter(models.Resource.id == 3).first()
if resource:
    print(f"\n2. 资源信息:")
    print(f"   - ID: {resource.id}")
    print(f"   - 名称: {resource.name}")

# 3. 检查 CNC机床-3 上已有的排程（可能占用了 02-04 的时间）
print(f"\n3. CNC机床-3 上已有的排程:")
existing_ops = db.query(models.Operation).filter(
    models.Operation.resource_id == 3,
    models.Operation.scheduled_start != None
).order_by(models.Operation.scheduled_start).all()

if existing_ops:
    for op in existing_ops:
        order = db.query(models.ProductionOrder).filter(models.ProductionOrder.id == op.order_id).first()
        order_number = order.order_number if order else "Unknown"
        print(f"   - 订单: {order_number}, 工序: {op.operation_name}")
        print(f"     时间: {op.scheduled_start} - {op.scheduled_end}")
else:
    print("   没有已排程的工序")

# 4. 检查 CNC机床-3 上 2026-02-04 这天是否有工序
print(f"\n4. 检查 2026-02-04 这天 CNC机床-3 的占用情况:")
day_start = datetime(2026, 2, 4, 0, 0, 0)
day_end = datetime(2026, 2, 4, 23, 59, 59)

ops_on_0204 = db.query(models.Operation).filter(
    models.Operation.resource_id == 3,
    models.Operation.scheduled_start != None,
    models.Operation.scheduled_start <= day_end,
    models.Operation.scheduled_end >= day_start
).all()

if ops_on_0204:
    print(f"   2026-02-04 有 {len(ops_on_0204)} 个工序占用:")
    for op in ops_on_0204:
        order = db.query(models.ProductionOrder).filter(models.ProductionOrder.id == op.order_id).first()
        order_number = order.order_number if order else "Unknown"
        print(f"   - 订单: {order_number}, 工序: {op.operation_name}")
        print(f"     时间: {op.scheduled_start} - {op.scheduled_end}")
else:
    print("   2026-02-04 没有已排程的工序")

# 5. 检查生产订单（PRD 开头的）是否占用了资源
print(f"\n5. 检查生产订单(PRD)在 CNC机床-3 上的占用:")
prd_ops = db.query(models.Operation).join(
    models.ProductionOrder,
    models.Operation.order_id == models.ProductionOrder.id
).filter(
    models.Operation.resource_id == 3,
    models.ProductionOrder.order_number.like('PRD%'),
    models.Operation.scheduled_start != None
).order_by(models.Operation.scheduled_start).all()

if prd_ops:
    for op in prd_ops:
        order = db.query(models.ProductionOrder).filter(models.ProductionOrder.id == op.order_id).first()
        print(f"   - 订单: {order.order_number}, 工序: {op.operation_name}")
        print(f"     时间: {op.scheduled_start} - {op.scheduled_end}")
        print(f"     订单类型: {order.order_type}, 状态: {order.status}")
else:
    print("   没有生产订单占用 CNC机床-3")

# 6. 检查算法中的 preserve_scheduled 设置
print(f"\n6. preserve_scheduled=True 的影响:")
print("   当 preserve_scheduled=True 时，已排程的订单/工序会被保留，")
print("   新排程会在已有排程之后寻找空闲时间槽。")

db.close()
