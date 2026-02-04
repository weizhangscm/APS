from datetime import datetime, timedelta
from app.database import SessionLocal
from app.scheduler.engine import SchedulingEngine
from app import models

db = SessionLocal()
engine = SchedulingEngine(db)

# 获取焊接工位-1的利用率数据
resource_id = 9  # 焊接工位-1

# 检查该资源的工作中心
resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
print(f"资源: {resource.name} (ID: {resource.id})")
print(f"工作中心ID: {resource.work_center_id}")

# 检查该工作中心下的所有待排程工序
print("\n该工作中心下的待排程工序:")
print("-" * 80)

pending_operations = db.query(models.Operation).join(
    models.RoutingOperation,
    models.Operation.routing_operation_id == models.RoutingOperation.id
).filter(
    models.Operation.resource_id == None,  # 未分配资源
    models.RoutingOperation.work_center_id == resource.work_center_id  # 通过工作中心匹配
).all()

print(f"共 {len(pending_operations)} 个待排程工序")

# 检查 2026-01-30 00:00-04:00 时间段
slot_start = datetime(2026, 1, 30, 0, 0, 0)
slot_end = datetime(2026, 1, 30, 4, 0, 0)

print(f"\n在 {slot_start} - {slot_end} 时间段内的工序:")
print("-" * 80)

total_hours = 0
for op in pending_operations:
    order = op.order
    if order and order.due_date:
        display_start = order.due_date.replace(hour=8, minute=0, second=0, microsecond=0)
        display_end = display_start + timedelta(hours=op.run_time)
        
        # 检查是否与时间槽重叠
        if display_start < slot_end and display_end > slot_start:
            overlap_start = max(display_start, slot_start)
            overlap_end = min(display_end, slot_end)
            hours = (overlap_end - overlap_start).total_seconds() / 3600
            total_hours += hours
            print(f"  订单: {order.order_number}")
            print(f"  工序: {op.sequence} {op.name}")
            print(f"  计划时间: {display_start} - {display_end}")
            print(f"  重叠时间: {hours:.2f} 小时")
            print()

print(f"总计工时: {total_hours:.2f} 小时")
print(f"利用率: {total_hours / 4 * 100:.1f}%")

# 同时检查已排程工序
print("\n\n已排程工序检查:")
print("-" * 80)

scheduled_operations = db.query(models.Operation).filter(
    models.Operation.resource_id == resource_id,
    models.Operation.scheduled_start != None,
    models.Operation.scheduled_end != None
).all()

print(f"共 {len(scheduled_operations)} 个已排程工序")

for op in scheduled_operations:
    if op.scheduled_start < slot_end and op.scheduled_end > slot_start:
        print(f"  工序: {op.sequence} {op.name}")
        print(f"  排程时间: {op.scheduled_start} - {op.scheduled_end}")
        print()

db.close()
