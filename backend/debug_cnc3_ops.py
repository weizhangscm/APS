"""检查CNC机床-3上的工序状态"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app import models
from app.scheduler.cache import schedule_cache

def check_cnc3():
    """检查CNC机床-3上的工序"""
    db = SessionLocal()
    
    print("=" * 60)
    print("检查 CNC机床-3 (ID=3) 上的工序")
    print("=" * 60)
    
    # 获取资源3上的所有工序
    operations = db.query(models.Operation).filter(
        models.Operation.resource_id == 3
    ).all()
    
    print(f"\n数据库中 CNC机床-3 上的工序数量: {len(operations)}")
    for op in operations:
        order = op.order
        print(f"  工序ID={op.id}, 订单={order.order_number if order else 'N/A'}, "
              f"名称={op.name}, 状态={op.status}")
        print(f"    scheduled_start={op.scheduled_start}, scheduled_end={op.scheduled_end}")
        if order:
            print(f"    订单交货期={order.due_date}, 订单状态={order.status}")
    
    # 检查缓存
    print(f"\n缓存状态:")
    print(f"  has_unsaved_changes: {schedule_cache.has_unsaved_changes}")
    
    cached_ops = schedule_cache.get_all_operations()
    print(f"  缓存中的工序总数: {len(cached_ops)}")
    
    # 检查缓存中分配到资源3的工序
    cnc3_cached = [op for op in cached_ops if op.resource_id == 3]
    print(f"  缓存中 CNC机床-3 的工序数: {len(cnc3_cached)}")
    for op in cnc3_cached:
        print(f"    工序ID={op.operation_id}, 开始={op.scheduled_start}, 结束={op.scheduled_end}")
    
    db.close()

if __name__ == '__main__':
    check_cnc3()
