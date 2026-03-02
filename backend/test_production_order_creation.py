"""
测试脚本：验证新创建的生产订单默认状态
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from app.database import get_db
from app import models


def test_production_order_creation():
    """测试通过代码创建生产订单的默认状态"""
    
    db = next(get_db())
    
    try:
        print("=" * 80)
        print("测试生产订单创建")
        print("=" * 80)
        
        # 获取一个产品和工艺路线
        product = db.query(models.Product).first()
        if not product:
            print("错误: 数据库中没有产品")
            return
        
        routing = db.query(models.Routing).filter(
            models.Routing.product_id == product.id,
            models.Routing.is_active == 1
        ).first()
        
        if not routing:
            print("错误: 产品没有工艺路线")
            return
        
        print(f"\n使用产品: {product.name} (ID: {product.id})")
        print(f"使用工艺路线: {routing.name}")
        
        # 创建一个测试生产订单
        test_order_number = f"TEST_PRD_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        test_order = models.ProductionOrder(
            order_number=test_order_number,
            order_type=models.OrderType.PRODUCTION.value,
            product_id=product.id,
            quantity=10,
            due_date=datetime.now() + timedelta(days=7),
            priority=3,
            confirmed_start=datetime.now() + timedelta(days=1),
            confirmed_end=datetime.now() + timedelta(days=3),
            description="测试生产订单",
            # 注意：不显式设置status，看默认值
        )
        
        db.add(test_order)
        db.commit()
        db.refresh(test_order)
        
        print(f"\n创建测试订单: {test_order_number}")
        print(f"订单类型: {test_order.order_type}")
        print(f"订单状态: {test_order.status}")
        
        # 为订单创建工序
        routing_ops = db.query(models.RoutingOperation).filter(
            models.RoutingOperation.routing_id == routing.id
        ).order_by(models.RoutingOperation.sequence).all()
        
        print(f"\n创建 {len(routing_ops)} 个工序:")
        
        for routing_op in routing_ops:
            # 获取工作中心的第一个资源
            resource = db.query(models.Resource).filter(
                models.Resource.work_center_id == routing_op.work_center_id
            ).first()
            
            operation = models.Operation(
                order_id=test_order.id,
                routing_operation_id=routing_op.id,
                resource_id=resource.id if resource else None,
                sequence=routing_op.sequence,
                name=routing_op.name,
                setup_time=routing_op.setup_time,
                run_time=routing_op.setup_time + (routing_op.run_time_per_unit * test_order.quantity),
                # 注意：不显式设置status，看默认值
            )
            
            db.add(operation)
            db.commit()
            db.refresh(operation)
            
            print(f"  工序 {operation.sequence:02d} - {operation.name}: 状态={operation.status}")
        
        # 验证结果
        print("\n" + "=" * 80)
        print("验证结果")
        print("=" * 80)
        
        # 注意：这里测试的是模型默认值，不是API端点的逻辑
        # 模型默认值是 CREATED，API端点会在创建时覆盖为 SCHEDULED
        
        if test_order.status == models.OrderStatus.CREATED.value:
            print("\n[注意] 直接通过模型创建的订单状态为 'created' (模型默认值)")
            print("      API端点会在创建时将生产订单状态设置为 'scheduled'")
        elif test_order.status == models.OrderStatus.SCHEDULED.value:
            print("\n[成功] 订单状态已设置为 'scheduled'")
        
        # 获取工序并检查状态
        operations = db.query(models.Operation).filter(
            models.Operation.order_id == test_order.id
        ).all()
        
        pending_ops = [op for op in operations if op.status == models.OperationStatus.PENDING.value]
        scheduled_ops = [op for op in operations if op.status == models.OperationStatus.SCHEDULED.value]
        
        print(f"\n工序状态分布:")
        print(f"  pending: {len(pending_ops)}")
        print(f"  scheduled: {len(scheduled_ops)}")
        
        if pending_ops:
            print("\n[注意] 直接通过模型创建的工序状态为 'pending' (模型默认值)")
            print("      API端点会在创建时将生产订单工序状态设置为 'scheduled'")
        
        # 清理测试数据
        print(f"\n清理测试订单: {test_order_number}")
        db.delete(test_order)
        db.commit()
        print("[完成] 测试订单已删除")
        
    except Exception as e:
        db.rollback()
        print(f"\n错误: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_production_order_creation()
