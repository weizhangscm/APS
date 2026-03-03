"""
修正计划订单的status字段
将订单status='scheduled'但工序status='pending'的计划订单改为status='created'
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal
from app import models

def fix_planned_order_status():
    """修正计划订单的status字段"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("修正计划订单状态")
        print("=" * 80)
        print()
        
        # 查找所有status='scheduled'的计划订单
        planned_orders = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PLANNED.value,
            models.ProductionOrder.status == models.OrderStatus.SCHEDULED.value
        ).all()
        
        print(f"找到 {len(planned_orders)} 个 status='scheduled' 的计划订单")
        print("-" * 80)
        print()
        
        if len(planned_orders) == 0:
            print("[OK] 没有需要修正的订单")
            return
        
        # 检查并修正
        fixed_count = 0
        
        for order in planned_orders:
            # 检查工序状态
            operations = db.query(models.Operation).filter(
                models.Operation.order_id == order.id
            ).all()
            
            has_pending = any(op.status == "pending" for op in operations)
            all_scheduled = all(op.status == "scheduled" for op in operations)
            
            # 如果有pending工序，订单应该是created状态
            if has_pending:
                print(f"[修正] {order.order_number}")
                print(f"  订单类型: 计划订单")
                print(f"  原状态: {order.status}")
                print(f"  工序状态: 有待排程工序")
                print(f"  新状态: created")
                
                order.status = models.OrderStatus.CREATED.value
                fixed_count += 1
                print()
            elif all_scheduled:
                print(f"[保持] {order.order_number}")
                print(f"  订单类型: 计划订单")
                print(f"  状态: {order.status}")
                print(f"  工序状态: 全部已排程")
                print(f"  说明: 订单和工序状态一致，无需修改")
                print()
        
        if fixed_count > 0:
            db.commit()
            print("-" * 80)
            print(f"[OK] 成功修正 {fixed_count} 个计划订单的状态")
        else:
            print("-" * 80)
            print("[OK] 所有计划订单状态正确，无需修改")
        
        print()
        
        # 验证结果
        print("验证修正结果:")
        print("-" * 80)
        
        # 检查是否还有不一致的计划订单
        remaining_inconsistent = 0
        all_orders = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PLANNED.value
        ).all()
        
        for order in all_orders:
            operations = db.query(models.Operation).filter(
                models.Operation.order_id == order.id
            ).all()
            
            has_pending = any(op.status == "pending" for op in operations)
            
            if order.status == "scheduled" and has_pending:
                remaining_inconsistent += 1
                print(f"[警告] {order.order_number} 仍然存在不一致")
        
        if remaining_inconsistent == 0:
            print("[OK] 所有计划订单的状态已与工序状态一致")
        else:
            print(f"[警告] 仍有 {remaining_inconsistent} 个订单存在不一致")
        
        print()
        
        # 统计最终结果
        print("最终统计:")
        print("-" * 80)
        
        planned_created = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PLANNED.value,
            models.ProductionOrder.status == models.OrderStatus.CREATED.value
        ).count()
        
        planned_scheduled = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PLANNED.value,
            models.ProductionOrder.status == models.OrderStatus.SCHEDULED.value
        ).count()
        
        production_scheduled = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PRODUCTION.value,
            models.ProductionOrder.status == models.OrderStatus.SCHEDULED.value
        ).count()
        
        total_scheduled = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.status == models.OrderStatus.SCHEDULED.value
        ).count()
        
        print(f"计划订单 - 待排程(created): {planned_created}")
        print(f"计划订单 - 已排程(scheduled): {planned_scheduled}")
        print(f"生产订单 - 已排程(scheduled): {production_scheduled}")
        print(f"总已排程订单数 (KPI将统计): {total_scheduled}")
        print()
        
        print("=" * 80)
        print("修正完成")
        print("=" * 80)
        
    except Exception as e:
        db.rollback()
        print(f"[错误] 修正失败: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_planned_order_status()
