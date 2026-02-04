from datetime import datetime, timedelta
from app.database import SessionLocal
from app.scheduler.engine import SchedulingEngine

db = SessionLocal()
engine = SchedulingEngine(db)

# 获取焊接工位-1的利用率数据
# 焊接工位-1 的 resource_id 是 9
result = engine.get_utilization_data(
    resource_ids=[9],  # 焊接工位-1
    start_date=datetime(2026, 1, 29, 0, 0, 0),
    end_date=datetime(2026, 2, 1, 0, 0, 0),
    zoom_level=1  # 4小时视图
)

print("焊接工位-1 的利用率数据:")
print("=" * 80)

for resource in result.get('data', []):
    print(f"\n资源: {resource['resource_name']} (ID: {resource['resource_id']})")
    print(f"时间槽数量: {len(resource['time_slots'])}")
    
    print("\n时间槽详情:")
    for slot in resource['time_slots']:
        utilization = slot['utilization']
        if utilization > 1:
            status = f"超载! ({utilization*100:.1f}%)"
        elif utilization > 0:
            status = f"正常 ({utilization*100:.1f}%)"
        else:
            status = "空闲"
        print(f"  {slot['start']} - {slot['end']}: {status}")

db.close()
