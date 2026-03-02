"""
检查订单状态分布
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from app.database import get_db
from app import models


def check_order_status():
    """检查所有订单的状态分布"""
    
    db = next(get_db())
    
    try:
        print("=" * 80)
        print("订单状态分布检查")
        print("=" * 80)
        
        # 1. 所有订单按类型和状态统计
        all_orders = db.query(models.ProductionOrder).all()
        
        print(f"\n订单总数: {len(all_orders)}")
        
        # 按类型分组
        planned_orders = [o for o in all_orders if o.order_type == models.OrderType.PLANNED.value]
        production_orders = [o for o in all_orders if o.order_type == models.OrderType.PRODUCTION.value]
        
        print(f"计划订单: {len(planned_orders)}")
        print(f"生产订单: {len(production_orders)}")
        
        # 计划订单状态分布
        print("\n计划订单状态分布:")
        planned_status = {}
        for o in planned_orders:
            planned_status[o.status] = planned_status.get(o.status, 0) + 1
        for status, count in planned_status.items():
            print(f"  {status}: {count}")
        
        # 生产订单状态分布
        print("\n生产订单状态分布:")
        prod_status = {}
        for o in production_orders:
            prod_status[o.status] = prod_status.get(o.status, 0) + 1
        for status, count in prod_status.items():
            print(f"  {status}: {count}")
        
        # 2. 检查状态为"created"的订单（未排程）
        print("\n" + "=" * 80)
        print("状态为 'created' 的订单（未排程）")
        print("=" * 80)
        
        created_orders = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.status == models.OrderStatus.CREATED.value
        ).all()
        
        print(f"\n找到 {len(created_orders)} 个状态为 'created' 的订单")
        
        if created_orders:
            print("\n订单列表:")
            for o in created_orders:
                print(f"  订单号: {o.order_number}, 类型: {o.order_type}, 状态: {o.status}")
        else:
            print("\n没有找到状态为 'created' 的订单")
            print("这就是为什么筛选'待排程'（created）时没有显示任何订单！")
        
        # 3. 显示前5个计划订单的详细信息
        print("\n" + "=" * 80)
        print("前5个计划订单详细信息")
        print("=" * 80)
        
        for order in planned_orders[:5]:
            print(f"\n订单号: {order.order_number}")
            print(f"  订单类型: {order.order_type}")
            print(f"  订单状态: {order.status}")
            print(f"  交货期: {order.due_date}")
            
            # 获取工序信息
            operations = db.query(models.Operation).filter(
                models.Operation.order_id == order.id
            ).all()
            
            if operations:
                op_status_dist = {}
                for op in operations:
                    op_status_dist[op.status] = op_status_dist.get(op.status, 0) + 1
                print(f"  工序状态: {op_status_dist}")
        
    finally:
        db.close()


if __name__ == "__main__":
    check_order_status()
