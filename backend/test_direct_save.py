# -*- coding: utf-8 -*-
"""
直接调用引擎测试，保存到数据库
"""
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app import models, schemas
from app.scheduler.engine import SchedulingEngine
from datetime import datetime

db = SessionLocal()

# 先查看当前 CNC机床-3 上的工序状态
print('=== Before scheduling ===')
ops = db.query(models.Operation).filter(models.Operation.resource_id == 3).all()
print(f'CNC-3 has {len(ops)} operations:')
for op in ops:
    order = db.query(models.ProductionOrder).filter(models.ProductionOrder.id == op.order_id).first()
    due_str = order.due_date.strftime('%Y-%m-%d') if order.due_date else 'None'
    print(f'  Op {op.id}: Order {order.order_number}, due_date={due_str}')

# 运行启发式（preview_mode=False 直接保存到数据库）
print()
print('=== Running heuristic with preview_mode=False ===')
engine = SchedulingEngine(db)
request = schemas.AutoPlanRequest(
    plan_type='heuristic',
    heuristic_id='stable_forward',
    optimizer_config={
        'display_start_date': '2026-02-04',
        'display_end_date': '2026-02-15',
        'order_internal_relation': '不考虑',
        'preview_mode': False  # 直接保存到数据库
    },
    resource_ids=[3]
)

result = engine.auto_plan(request)

print()
print('=== Scheduling Result ===')
print('scheduled_orders:', result.get('scheduled_orders'))
print('scheduled_operations:', result.get('scheduled_operations'))
print('_engine_version:', result.get('_engine_version'))
print('_filtered_ops_count:', result.get('_filtered_ops_count'))

# 查看排程后的工序状态
print()
print('=== Scheduled Operations ===')
for detail in result.get('details', []):
    if detail.get('success'):
        order_num = detail.get('order_number', 'Unknown')
        for op_info in detail.get('operations', []):
            print(f'  Order {order_num}, Op {op_info["operation_id"]}: {op_info["start"]} - {op_info["end"]}')

db.close()
