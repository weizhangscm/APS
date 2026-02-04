"""检查待排程工序"""
import sys
sys.path.insert(0, '.')

from datetime import datetime, timedelta
from app.database import SessionLocal
from app import models

def check_pending_ops():
    """检查CNC机床上的待排程工序"""
    db = SessionLocal()
    
    print("=" * 60)
    print("CNC机床上的待排程工序检查")
    print("=" * 60)
    
    # 获取资源
    resources = db.query(models.Resource).filter(
        models.Resource.name.in_(['CNC机床-1', 'CNC机床-3'])
    ).all()
    
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now() + timedelta(days=30)
    
    for resource in resources:
        print(f"\n资源: {resource.name} (ID={resource.id})")
        
        # 查找该资源上的待排程工序（scheduled_start=None，但due_date在范围内）
        from sqlalchemy import or_
        pending_ops = db.query(models.Operation).join(
            models.ProductionOrder,
            models.Operation.order_id == models.ProductionOrder.id
        ).filter(
            models.Operation.resource_id == resource.id,
            models.Operation.scheduled_start == None,
            models.ProductionOrder.due_date >= start_date,
            models.ProductionOrder.due_date <= end_date
        ).all()
        
        print(f"  待排程工序数量: {len(pending_ops)}")
        for op in pending_ops:
            order = op.order
            print(f"    工序ID={op.id}, 订单={order.order_number}, "
                  f"名称={op.name}, due_date={order.due_date}")

    db.close()

if __name__ == '__main__':
    check_pending_ops()
