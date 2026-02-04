from datetime import datetime, timedelta
from app.database import SessionLocal
from app.scheduler.engine import SchedulingEngine
from app import models

db = SessionLocal()

# 检查焊接工位-1的工作中心
resource = db.query(models.Resource).filter(models.Resource.id == 9).first()
print(f"资源: {resource.name} (ID: {resource.id})")
print(f"工作中心ID: {resource.work_center_id}")

# 检查所有工作中心ID为2的资源
print("\n工作中心ID=2 的所有资源:")
resources_in_wc = db.query(models.Resource).filter(models.Resource.work_center_id == 2).all()
for r in resources_in_wc:
    print(f"  {r.name} (ID: {r.id})")

# 检查待排程工序通过工作中心匹配到的数据
print("\n检查待排程工序:")
pending_ops = db.query(models.Operation).join(
    models.RoutingOperation,
    models.Operation.routing_operation_id == models.RoutingOperation.id
).filter(
    models.Operation.resource_id == None,
    models.RoutingOperation.work_center_id == 2  # 钣金车间
).all()

print(f"共 {len(pending_ops)} 个待排程工序匹配到工作中心ID=2")

# 检查这些工序的订单交货日期
print("\n这些工序的订单信息:")
orders_checked = set()
for op in pending_ops:
    order = op.order
    if order and order.id not in orders_checked:
        orders_checked.add(order.id)
        display_start = order.due_date.replace(hour=8, minute=0, second=0, microsecond=0) if order.due_date else None
        print(f"  订单: {order.order_number}, 交货日期: {order.due_date}, 显示开始: {display_start}")

# 直接调用API检查返回数据
print("\n\n调用 get_utilization_data API:")
engine = SchedulingEngine(db)
result = engine.get_utilization_data(
    resource_ids=[9],
    start_date=datetime(2026, 1, 29, 0, 0, 0),
    end_date=datetime(2026, 1, 31, 0, 0, 0),
    zoom_level=1
)

for res in result.get('data', []):
    print(f"\n资源: {res['resource_name']}")
    for slot in res['time_slots']:
        if slot['utilization'] > 0:
            print(f"  {slot['start']} - {slot['end']}: {slot['utilization']*100:.1f}%")

db.close()
