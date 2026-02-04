"""取消交货期在2026-02-09及以后的订单的排程"""
import sys
sys.path.insert(0, '.')

from datetime import datetime
from app.database import SessionLocal
from app import models

def cancel_schedules():
    """取消交货期在2026-02-09及以后的订单的排程"""
    db = SessionLocal()
    
    cutoff_date = datetime(2026, 2, 9, 0, 0, 0)
    
    print("=" * 60)
    print(f"取消交货期在 {cutoff_date.date()} 及以后的订单排程")
    print("=" * 60)
    
    # 查找交货期在2026-02-09及以后的计划订单
    orders = db.query(models.ProductionOrder).filter(
        models.ProductionOrder.order_type == models.OrderType.PLANNED.value,
        models.ProductionOrder.due_date >= cutoff_date
    ).all()
    
    print(f"\n找到 {len(orders)} 个符合条件的计划订单")
    
    # 统计
    orders_cancelled = 0
    operations_cancelled = 0
    
    for order in orders:
        print(f"\n处理订单: {order.order_number}, 交货期: {order.due_date.date()}, 当前状态: {order.status}")
        
        # 查找该订单的所有工序
        operations = db.query(models.Operation).filter(
            models.Operation.order_id == order.id
        ).all()
        
        order_had_schedule = False
        for op in operations:
            if op.scheduled_start or op.scheduled_end:
                order_had_schedule = True
                print(f"  取消工序: {op.name} (ID={op.id}), 原排程: {op.scheduled_start} - {op.scheduled_end}")
                op.scheduled_start = None
                op.scheduled_end = None
                op.changeover_time = None
                op.status = models.OperationStatus.PENDING.value
                operations_cancelled += 1
        
        # 如果订单状态是 scheduled，改为 created
        if order.status == models.OrderStatus.SCHEDULED.value:
            order.status = models.OrderStatus.CREATED.value
            orders_cancelled += 1
            print(f"  订单状态已从 scheduled 改为 created")
        elif order_had_schedule:
            orders_cancelled += 1
    
    # 提交更改
    db.commit()
    
    print("\n" + "=" * 60)
    print(f"完成! 取消了 {orders_cancelled} 个订单的排程，共 {operations_cancelled} 道工序")
    print("=" * 60)
    
    db.close()

if __name__ == '__main__':
    cancel_schedules()
