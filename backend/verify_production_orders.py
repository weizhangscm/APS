"""
验证脚本：检查生产订单的状态
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from app.database import get_db
from app import models


def verify_production_orders():
    """验证生产订单状态"""
    
    db = next(get_db())
    
    try:
        print("=" * 80)
        print("验证生产订单状态")
        print("=" * 80)
        
        # 1. 生产订单统计
        production_orders = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PRODUCTION.value
        ).all()
        
        print(f"\n生产订单总数: {len(production_orders)}")
        
        # 按状态分组
        status_counts = {}
        for order in production_orders:
            status_counts[order.status] = status_counts.get(order.status, 0) + 1
        
        print("\n生产订单状态分布:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
        
        # 2. 显示前3个生产订单的详细信息
        print("\n前3个生产订单示例:")
        for order in production_orders[:3]:
            print(f"\n订单号: {order.order_number}")
            print(f"  订单类型: {order.order_type}")
            print(f"  订单状态: {order.status}")
            print(f"  产品ID: {order.product_id}")
            
            # 获取该订单的工序
            operations = db.query(models.Operation).filter(
                models.Operation.order_id == order.id
            ).order_by(models.Operation.sequence).all()
            
            print(f"  工序数量: {len(operations)}")
            
            # 工序状态统计
            op_status_counts = {}
            for op in operations:
                op_status_counts[op.status] = op_status_counts.get(op.status, 0) + 1
            
            print(f"  工序状态分布: {op_status_counts}")
        
        # 3. 计划订单统计（确保未受影响）
        print("\n" + "=" * 80)
        print("验证计划订单未受影响")
        print("=" * 80)
        
        planned_orders = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PLANNED.value
        ).all()
        
        print(f"\n计划订单总数: {len(planned_orders)}")
        
        # 按状态分组
        planned_status_counts = {}
        for order in planned_orders:
            planned_status_counts[order.status] = planned_status_counts.get(order.status, 0) + 1
        
        print("\n计划订单状态分布:")
        for status, count in planned_status_counts.items():
            print(f"  {status}: {count}")
        
        # 4. 总结
        print("\n" + "=" * 80)
        print("总结")
        print("=" * 80)
        
        all_prod_scheduled = all(o.status == models.OrderStatus.SCHEDULED.value for o in production_orders)
        print(f"\n所有生产订单状态为已排程: {all_prod_scheduled}")
        
        # 检查所有生产订单的工序
        all_prod_ops_scheduled = True
        for order in production_orders:
            operations = db.query(models.Operation).filter(
                models.Operation.order_id == order.id
            ).all()
            for op in operations:
                if op.status != models.OperationStatus.SCHEDULED.value:
                    all_prod_ops_scheduled = False
                    break
            if not all_prod_ops_scheduled:
                break
        
        print(f"所有生产订单工序状态为已排程: {all_prod_ops_scheduled}")
        
        if all_prod_scheduled and all_prod_ops_scheduled:
            print("\n[成功] 所有生产订单及其工序的状态都已正确设置为已排程！")
        else:
            print("\n[警告] 部分生产订单或工序状态未正确设置")
        
    finally:
        db.close()


if __name__ == "__main__":
    verify_production_orders()
