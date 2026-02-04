"""调试启发式排程问题"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app import models

def check_operations_on_resources():
    """检查选中资源上的工序"""
    db = SessionLocal()
    
    # 选中的资源IDs (CNC机床-1, CNC机床-3)
    # 先获取资源信息
    resources = db.query(models.Resource).filter(
        models.Resource.name.in_(['CNC机床-1', 'CNC机床-3'])
    ).all()
    
    print("=" * 60)
    print("选中的资源:")
    for r in resources:
        print(f"  ID={r.id}, 名称={r.name}, 工作中心ID={r.work_center_id}")
    
    resource_ids = [r.id for r in resources]
    print(f"\n资源IDs: {resource_ids}")
    
    # 查找这些资源上的工序
    operations = db.query(models.Operation).filter(
        models.Operation.resource_id.in_(resource_ids)
    ).all()
    
    print(f"\n选中资源上的工序数量: {len(operations)}")
    for op in operations[:20]:  # 只显示前20个
        order = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.id == op.order_id
        ).first()
        order_status = order.status if order else 'N/A'
        print(f"  工序ID={op.id}, 订单={order.order_number if order else 'N/A'}, "
              f"资源ID={op.resource_id}, 状态={op.status}, "
              f"排程开始={op.scheduled_start}, 订单状态={order_status}")
    
    # 检查这些工序所属的订单
    order_ids = list(set([op.order_id for op in operations]))
    print(f"\n这些工序所属的订单数量: {len(order_ids)}")
    
    orders = db.query(models.ProductionOrder).filter(
        models.ProductionOrder.id.in_(order_ids)
    ).all()
    
    print("\n订单列表:")
    for o in orders:
        print(f"  订单号={o.order_number}, 状态={o.status}, 类型={o.order_type}")
    
    # 检查计划订单
    planned_orders = [o for o in orders if o.order_type == models.OrderType.PLANNED.value]
    print(f"\n其中计划订单数量: {len(planned_orders)}")
    
    # 检查已排程的计划订单
    scheduled_planned = [o for o in planned_orders if o.status == models.OrderStatus.SCHEDULED.value]
    print(f"已排程的计划订单数量: {len(scheduled_planned)}")
    
    db.close()

if __name__ == '__main__':
    check_operations_on_resources()
