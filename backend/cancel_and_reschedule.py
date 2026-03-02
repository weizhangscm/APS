# -*- coding: utf-8 -*-
"""
1. 取消交货期 2026-02-09 及以后的计划订单的排程
2. 重新运行启发式并保存到数据库
3. 输出排程结果
"""
import sys
sys.path.insert(0, '.')
from datetime import datetime
from app.database import SessionLocal
from app import models, schemas
from app.scheduler.engine import SchedulingEngine

db = SessionLocal()

# Step 1: 取消交货期 2026-02-09 及以后的计划订单的排程
print('=== Step 1: Cancel scheduling for orders with due_date >= 2026-02-09 ===')
cutoff_date = datetime(2026, 2, 9)

# 查找需要取消的订单
orders_to_cancel = db.query(models.ProductionOrder).filter(
    models.ProductionOrder.due_date >= cutoff_date,
    models.ProductionOrder.order_type == 'planned'
).all()

print(f'Found {len(orders_to_cancel)} orders to cancel:')
for order in orders_to_cancel:
    print(f'  {order.order_number} (due_date={order.due_date.strftime("%Y-%m-%d")})')
    
    # 取消该订单的所有工序排程
    ops = db.query(models.Operation).filter(models.Operation.order_id == order.id).all()
    for op in ops:
        op.scheduled_start = None
        op.scheduled_end = None
        op.status = 'pending'

db.commit()
print('Cancelled.')

# Step 2: 运行启发式并保存到数据库
print()
print('=== Step 2: Run heuristic and save to database ===')
engine = SchedulingEngine(db)
request = schemas.AutoPlanRequest(
    plan_type='heuristic',
    heuristic_id='stable_forward',
    optimizer_config={
        'display_start_date': '2026-02-04',
        'display_end_date': '2026-02-15',
        'order_internal_relation': '不考虑',
        'preview_mode': False
    },
    resource_ids=[3]
)

result = engine.auto_plan(request)
print(f'scheduled_orders: {result.get("scheduled_orders")}')
print(f'scheduled_operations: {result.get("scheduled_operations")}')

# Step 3: 输出排程结果
print()
print('=== Step 3: CNC-3 Scheduling Result ===')
print()

ops = db.query(models.Operation).filter(models.Operation.resource_id == 3).all()
scheduled_ops = [op for op in ops if op.scheduled_start]
unscheduled_ops = [op for op in ops if not op.scheduled_start]

print('Scheduled:')
for op in sorted(scheduled_ops, key=lambda x: x.scheduled_start):
    order = db.query(models.ProductionOrder).filter(models.ProductionOrder.id == op.order_id).first()
    due = order.due_date.strftime('%Y-%m-%d') if order.due_date else 'None'
    start = op.scheduled_start.strftime('%Y-%m-%d %H:%M:%S')
    end = op.scheduled_end.strftime('%Y-%m-%d %H:%M:%S')
    print(f'  {order.order_number} | due: {due} | {start} ~ {end}')

if unscheduled_ops:
    print()
    print('Unscheduled:')
    for op in unscheduled_ops:
        order = db.query(models.ProductionOrder).filter(models.ProductionOrder.id == op.order_id).first()
        due = order.due_date.strftime('%Y-%m-%d') if order.due_date else 'None'
        print(f'  {order.order_number} | due: {due}')

db.close()
