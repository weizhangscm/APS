# -*- coding: utf-8 -*-
"""
重置排程数据并用新算法重新排程
"""
import sys
sys.path.insert(0, '.')

from datetime import datetime
from app.database import SessionLocal
from app import models
from app.scheduler.engine import SchedulingEngine

db = SessionLocal()

try:
    # 1. 清除所有工序的排程数据（保留资源分配）
    print("=" * 80)
    print("1. 清除现有排程数据...")
    print("=" * 80)
    
    operations = db.query(models.Operation).all()
    for op in operations:
        op.scheduled_start = None
        op.scheduled_end = None
        op.changeover_time = None
        op.status = models.OperationStatus.PENDING.value
    
    # 重置计划订单状态
    planned_orders = db.query(models.ProductionOrder).filter(
        models.ProductionOrder.order_type == models.OrderType.PLANNED.value
    ).all()
    for order in planned_orders:
        order.status = models.OrderStatus.CREATED.value
    
    db.commit()
    print(f"  已清除 {len(operations)} 个工序的排程数据")
    print(f"  已重置 {len(planned_orders)} 个计划订单的状态")
    
    # 2. 使用新算法重新排程
    print("\n" + "=" * 80)
    print("2. 使用新算法重新排程...")
    print("=" * 80)
    
    engine = SchedulingEngine(db)
    
    # 获取所有计划订单
    orders_to_schedule = db.query(models.ProductionOrder).filter(
        models.ProductionOrder.order_type == models.OrderType.PLANNED.value,
        models.ProductionOrder.status != models.OrderStatus.SCHEDULED.value
    ).all()
    
    print(f"  待排程订单数: {len(orders_to_schedule)}")
    
    # 执行稳定向前排程
    from app import schemas
    request = schemas.AutoPlanRequest(
        plan_type='heuristic',
        heuristic_id='stable_forward',
        optimizer_config={
            'finite_capacity': True,
            'resolve_backlog': True,
            'resolve_overload': True,
            'preserve_scheduled': True,
            'sorting_rule': 'EDD',
            'planning_horizon': 90
        }
    )
    result = engine.auto_plan(request)
    
    print(f"\n  排程结果:")
    print(f"    - 已排程订单: {result.get('scheduled_orders', 0)}")
    print(f"    - 已排程工序: {result.get('scheduled_operations', 0)}")
    
    # 3. 验证排程结果
    print("\n" + "=" * 80)
    print("3. 验证排程结果...")
    print("=" * 80)
    
    # 查询工序的排程时间分布
    from sqlalchemy import func
    
    scheduled_ops = db.query(models.Operation).filter(
        models.Operation.scheduled_start != None
    ).all()
    
    if scheduled_ops:
        min_start = min(op.scheduled_start for op in scheduled_ops)
        max_end = max(op.scheduled_end for op in scheduled_ops)
        
        print(f"  已排程工序数: {len(scheduled_ops)}")
        print(f"  最早开始时间: {min_start}")
        print(f"  最晚结束时间: {max_end}")
        print(f"  时间跨度: {(max_end - min_start).days} 天")
    
    # 检查是否还有超过2026年3月的排程
    late_ops = [op for op in scheduled_ops if op.scheduled_start and op.scheduled_start > datetime(2026, 3, 31)]
    print(f"\n  2026-03-31 之后的工序: {len(late_ops)}")
    
    if late_ops:
        print("  警告：仍有工序排到了3月之后！")
        for op in late_ops[:5]:
            order = op.order
            print(f"    - {order.order_number} 工序{op.sequence}: {op.scheduled_start}")
    else:
        print("  成功：所有工序都在合理时间范围内！")
    
    db.commit()
    print("\n排程完成！")
    
except Exception as e:
    db.rollback()
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
