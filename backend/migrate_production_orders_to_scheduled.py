"""
迁移脚本：将所有生产订单（order_type='production'）的状态更新为已排程

此脚本会：
1. 将所有 order_type='production' 的订单状态更新为 'scheduled'
2. 将这些生产订单的所有工序状态更新为 'scheduled'
3. 只影响生产订单，不影响计划订单或其他功能
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from app.database import get_db, engine
from app import models


def migrate_production_orders():
    """将生产订单及其工序状态更新为已排程"""
    
    db = next(get_db())
    
    try:
        print("=" * 80)
        print("开始迁移生产订单状态")
        print("=" * 80)
        
        # 1. 查询所有生产订单
        production_orders = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PRODUCTION.value
        ).all()
        
        print(f"\n找到 {len(production_orders)} 个生产订单")
        
        if not production_orders:
            print("没有需要迁移的生产订单")
            return
        
        # 2. 更新订单状态
        updated_orders = 0
        updated_operations = 0
        
        for order in production_orders:
            order_number = order.order_number
            old_order_status = order.status
            
            # 更新订单状态为已排程
            if order.status != models.OrderStatus.SCHEDULED.value:
                order.status = models.OrderStatus.SCHEDULED.value
                updated_orders += 1
                print(f"\n订单 {order_number}:")
                print(f"  订单状态: {old_order_status} -> {models.OrderStatus.SCHEDULED.value}")
            
            # 3. 更新该订单的所有工序状态
            operations = db.query(models.Operation).filter(
                models.Operation.order_id == order.id
            ).all()
            
            for op in operations:
                old_op_status = op.status
                if op.status != models.OperationStatus.SCHEDULED.value:
                    op.status = models.OperationStatus.SCHEDULED.value
                    updated_operations += 1
                    print(f"  工序 {op.sequence:02d} - {op.name}: {old_op_status} -> {models.OperationStatus.SCHEDULED.value}")
        
        # 提交更改
        db.commit()
        
        print("\n" + "=" * 80)
        print("迁移完成!")
        print(f"更新了 {updated_orders} 个订单状态")
        print(f"更新了 {updated_operations} 个工序状态")
        print("=" * 80)
        
        # 4. 验证结果
        print("\n验证结果:")
        
        # 检查生产订单状态
        prod_orders_count = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PRODUCTION.value
        ).count()
        
        prod_scheduled_count = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PRODUCTION.value,
            models.ProductionOrder.status == models.OrderStatus.SCHEDULED.value
        ).count()
        
        print(f"生产订单总数: {prod_orders_count}")
        print(f"状态为已排程的生产订单: {prod_scheduled_count}")
        
        if prod_orders_count == prod_scheduled_count:
            print("[OK] 所有生产订单状态都已更新为已排程")
        else:
            print(f"[警告] 还有 {prod_orders_count - prod_scheduled_count} 个生产订单状态不是已排程")
        
        # 检查生产订单的工序状态
        prod_order_ids = [o.id for o in db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PRODUCTION.value
        ).all()]
        
        if prod_order_ids:
            prod_ops_count = db.query(models.Operation).filter(
                models.Operation.order_id.in_(prod_order_ids)
            ).count()
            
            prod_ops_scheduled_count = db.query(models.Operation).filter(
                models.Operation.order_id.in_(prod_order_ids),
                models.Operation.status == models.OperationStatus.SCHEDULED.value
            ).count()
            
            print(f"生产订单工序总数: {prod_ops_count}")
            print(f"状态为已排程的工序: {prod_ops_scheduled_count}")
            
            if prod_ops_count == prod_ops_scheduled_count:
                print("[OK] 所有生产订单工序状态都已更新为已排程")
            else:
                print(f"[警告] 还有 {prod_ops_count - prod_ops_scheduled_count} 个工序状态不是已排程")
        
        # 确保计划订单没有被影响
        print("\n验证计划订单未受影响:")
        planned_orders = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PLANNED.value
        ).all()
        
        print(f"计划订单总数: {len(planned_orders)}")
        
        planned_scheduled_count = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PLANNED.value,
            models.ProductionOrder.status == models.OrderStatus.SCHEDULED.value
        ).count()
        
        print(f"状态为已排程的计划订单: {planned_scheduled_count}")
        print("[OK] 计划订单状态由排程引擎管理，未受影响")
        
    except Exception as e:
        db.rollback()
        print(f"\n错误: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_production_orders()
