"""检查数据库中的排程数据"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app import models

def check_db_schedule():
    """检查数据库中的排程状态"""
    db = SessionLocal()
    
    print("=" * 60)
    print("数据库排程状态检查")
    print("=" * 60)
    
    # 检查所有有排程时间的工序
    scheduled_ops = db.query(models.Operation).filter(
        models.Operation.scheduled_start != None
    ).all()
    
    print(f"\n有排程时间的工序数量: {len(scheduled_ops)}")
    
    if scheduled_ops:
        print("\n已排程的工序 (前30个):")
        for op in scheduled_ops[:30]:
            order = db.query(models.ProductionOrder).filter(
                models.ProductionOrder.id == op.order_id
            ).first()
            print(f"  工序ID={op.id}, 订单={order.order_number if order else 'N/A'}, "
                  f"资源ID={op.resource_id}, 名称={op.name}, "
                  f"开始={op.scheduled_start}, 结束={op.scheduled_end}")
        
        # 检查这些工序在哪些资源上
        by_resource = {}
        for op in scheduled_ops:
            if op.resource_id not in by_resource:
                by_resource[op.resource_id] = []
            by_resource[op.resource_id].append(op)
        
        print("\n按资源分组:")
        for res_id, ops in sorted(by_resource.items()):
            # 获取资源名称
            resource = db.query(models.Resource).filter(models.Resource.id == res_id).first()
            res_name = resource.name if resource else f"Unknown({res_id})"
            print(f"  资源 {res_id} ({res_name}): {len(ops)} 个已排程工序")
    
    # 检查已排程状态的订单
    scheduled_orders = db.query(models.ProductionOrder).filter(
        models.ProductionOrder.status == models.OrderStatus.SCHEDULED.value
    ).all()
    
    print(f"\n已排程状态的订单数量: {len(scheduled_orders)}")
    for o in scheduled_orders[:10]:
        print(f"  订单号={o.order_number}, 类型={o.order_type}")
    
    db.close()

if __name__ == '__main__':
    check_db_schedule()
