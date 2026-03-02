# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app import models

db = SessionLocal()

# 查询 CNC机床-3 上的所有工序
ops = db.query(models.Operation).filter(models.Operation.resource_id == 3).all()

print('CNC机床-3 排程结果:')
print()

for op in sorted(ops, key=lambda x: x.scheduled_start if x.scheduled_start else x.id):
    order = db.query(models.ProductionOrder).filter(models.ProductionOrder.id == op.order_id).first()
    due = order.due_date.strftime('%Y-%m-%d') if order.due_date else 'None'
    start = op.scheduled_start.strftime('%Y-%m-%d %H:%M:%S') if op.scheduled_start else 'None'
    end = op.scheduled_end.strftime('%Y-%m-%d %H:%M:%S') if op.scheduled_end else 'None'
    print(f'{order.order_number} | {due} | {start} | {end}')

db.close()
