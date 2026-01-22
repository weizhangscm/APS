from app.database import SessionLocal
from app import models

db = SessionLocal()

# 检查 PLN20260011 的所有工序
print('=== Order PLN20260011 Operations ===')
order = db.query(models.ProductionOrder).filter(models.ProductionOrder.order_number == 'PLN20260011').first()
if order:
    print(f'Order: {order.order_number}')
    ops = db.query(models.Operation).filter(models.Operation.order_id == order.id).order_by(models.Operation.sequence).all()
    for op in ops:
        res = op.resource
        res_name = res.name if res else 'None'
        print(f'  {op.sequence} {op.name}')
        print(f'    Resource: {res_name} (ID: {op.resource_id})')
        if op.scheduled_start:
            print(f'    Time: {op.scheduled_start.strftime("%m-%d %H:%M")} ~ {op.scheduled_end.strftime("%m-%d %H:%M")}')
        print()

print()
print('=== All Resources ===')
resources = db.query(models.Resource).all()
for r in resources:
    print(f'  {r.id}: {r.name}')

db.close()
