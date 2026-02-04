"""检查工序所属订单的类型"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app import models

def check_order_types():
    """检查CNC机床上工序所属订单的类型"""
    db = SessionLocal()
    
    print("=" * 60)
    print("检查工序所属订单的类型")
    print("=" * 60)
    
    # 获取资源
    resources = db.query(models.Resource).filter(
        models.Resource.name.in_(['CNC机床-1', 'CNC机床-3'])
    ).all()
    resource_ids = [r.id for r in resources]
    print(f"资源IDs: {resource_ids}")
    
    # 查找这些资源上的所有工序
    target_operations = db.query(models.Operation).filter(
        models.Operation.resource_id.in_(resource_ids)
    ).all()
    
    print(f"\n选中资源上的工序数量: {len(target_operations)}")
    
    # 按订单类型分组
    order_ids = list(set([op.order_id for op in target_operations]))
    print(f"涉及的订单数量: {len(order_ids)}")
    
    planned_count = 0
    production_count = 0
    
    for order_id in order_ids:
        order = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.id == order_id
        ).first()
        if order:
            if order.order_type == models.OrderType.PLANNED.value:
                planned_count += 1
            else:
                production_count += 1
    
    print(f"\n订单类型统计:")
    print(f"  计划订单 (planned): {planned_count}")
    print(f"  生产订单 (production): {production_count}")
    
    # 检查计划订单的状态
    print(f"\n计划订单详情:")
    planned_orders = db.query(models.ProductionOrder).filter(
        models.ProductionOrder.id.in_(order_ids),
        models.ProductionOrder.order_type == models.OrderType.PLANNED.value
    ).all()
    
    for o in planned_orders:
        print(f"  订单号={o.order_number}, 状态={o.status}")
    
    db.close()

if __name__ == '__main__':
    check_order_types()
