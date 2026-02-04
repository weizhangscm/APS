"""检查PLN20260029订单的状态"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app import models
from app.scheduler.cache import schedule_cache

def check_pln29():
    """检查PLN20260029订单"""
    db = SessionLocal()
    
    print("=" * 60)
    print("检查 PLN20260029 订单")
    print("=" * 60)
    
    # 查找订单
    order = db.query(models.ProductionOrder).filter(
        models.ProductionOrder.order_number == 'PLN20260029'
    ).first()
    
    if not order:
        print("订单不存在！")
        return
    
    print(f"\n订单信息:")
    print(f"  ID: {order.id}")
    print(f"  订单号: {order.order_number}")
    print(f"  类型: {order.order_type}")
    print(f"  状态: {order.status}")
    print(f"  交货期: {order.due_date}")
    
    # 查找工序
    operations = db.query(models.Operation).filter(
        models.Operation.order_id == order.id
    ).order_by(models.Operation.sequence).all()
    
    print(f"\n工序列表 ({len(operations)} 个):")
    for op in operations:
        resource_name = "未分配"
        if op.resource_id:
            resource = db.query(models.Resource).filter(models.Resource.id == op.resource_id).first()
            resource_name = resource.name if resource else f"ID={op.resource_id}"
        
        print(f"  工序ID={op.id}, 序号={op.sequence}, 名称={op.name}")
        print(f"    资源: {resource_name} (ID={op.resource_id})")
        print(f"    状态: {op.status}")
        print(f"    排程开始: {op.scheduled_start}")
        print(f"    排程结束: {op.scheduled_end}")
    
    # 检查缓存
    print(f"\n缓存状态:")
    print(f"  有未保存更改: {schedule_cache.has_unsaved_changes}")
    
    cached_ops = schedule_cache.get_all_operations()
    print(f"  缓存中的工序数: {len(cached_ops)}")
    
    # 查找缓存中PLN20260029的工序
    for cached_op in cached_ops:
        if cached_op.order_id == order.id:
            print(f"  缓存中的工序: ID={cached_op.operation_id}, 资源={cached_op.resource_id}, "
                  f"开始={cached_op.scheduled_start}, 结束={cached_op.scheduled_end}")
    
    db.close()

if __name__ == '__main__':
    check_pln29()
