# -*- coding: utf-8 -*-
"""
Test: verify production orders are loaded as resource slots
"""
import sys
sys.path.insert(0, '.')
from datetime import datetime, timedelta
from app.database import SessionLocal
from app import models, schemas
from app.scheduler.engine import SchedulingEngine

db = SessionLocal()

# First, cancel all planned order schedules
print('=== Cancelling all planned order schedules ===')
orders = db.query(models.ProductionOrder).filter(
    models.ProductionOrder.order_type == 'planned'
).all()
for order in orders:
    ops = db.query(models.Operation).filter(models.Operation.order_id == order.id).all()
    for op in ops:
        op.scheduled_start = None
        op.scheduled_end = None
        op.status = 'pending'
    order.status = 'created'
db.commit()

# Run heuristic on CNC-1 (resource_id=1)
print()
print('=== Running heuristic on CNC-1 ===')
engine = SchedulingEngine(db)
request = schemas.AutoPlanRequest(
    plan_type='heuristic',
    heuristic_id='stable_forward',
    optimizer_config={
        'display_start_date': '2026-02-02',
        'display_end_date': '2026-02-22',
        'order_internal_relation': '不考虑',
        'preview_mode': False
    },
    resource_ids=[1]
)

result = engine.auto_plan(request)
print(f'scheduled_orders: {result.get("scheduled_orders")}')

# Show results
print()
print('=== CNC-1 Production Orders (fixed) ===')
prod_ops = db.query(models.Operation).join(
    models.ProductionOrder,
    models.Operation.order_id == models.ProductionOrder.id
).filter(
    models.Operation.resource_id == 1,
    models.ProductionOrder.order_type == 'production'
).all()

for op in prod_ops:
    order = db.query(models.ProductionOrder).filter(models.ProductionOrder.id == op.order_id).first()
    cs = order.confirmed_start.strftime('%Y-%m-%d %H:%M') if order.confirmed_start else 'None'
    ce = order.confirmed_end.strftime('%Y-%m-%d %H:%M') if order.confirmed_end else 'None'
    print(f'  {order.order_number} - {op.name}: confirmed={cs} ~ {ce}, run_time={op.run_time}h')

print()
print('=== CNC-1 Planned Orders (scheduled) ===')
plan_ops = db.query(models.Operation).join(
    models.ProductionOrder,
    models.Operation.order_id == models.ProductionOrder.id
).filter(
    models.Operation.resource_id == 1,
    models.ProductionOrder.order_type == 'planned',
    models.Operation.scheduled_start != None
).order_by(models.Operation.scheduled_start).all()

for op in plan_ops:
    order = db.query(models.ProductionOrder).filter(models.ProductionOrder.id == op.order_id).first()
    start = op.scheduled_start.strftime('%Y-%m-%d %H:%M')
    end = op.scheduled_end.strftime('%Y-%m-%d %H:%M')
    print(f'  {order.order_number} - {op.name}: {start} ~ {end}')

db.close()
