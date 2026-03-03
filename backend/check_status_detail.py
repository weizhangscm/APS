"""
详细检查订单和工序状态，找出数据不一致的根本原因
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal
from app import models

def check_detailed_status():
    db = SessionLocal()
    
    try:
        all_orders = db.query(models.ProductionOrder).all()
        
        print("=" * 100)
        print("订单和工序状态详细分析")
        print("=" * 100)
        print()
        
        # 分类统计
        planned_correct = []  # 计划订单：订单created，工序pending
        planned_inconsistent = []  # 计划订单：订单scheduled，工序pending（不一致）
        production_correct = []  # 生产订单：订单scheduled，工序scheduled
        
        for order in all_orders:
            operations = db.query(models.Operation).filter(
                models.Operation.order_id == order.id
            ).all()
            
            has_pending = any(op.status == "pending" for op in operations)
            all_scheduled = all(op.status == "scheduled" for op in operations)
            
            if order.order_type == "planned":
                if order.status == "created" and has_pending:
                    planned_correct.append((order, operations))
                elif order.status == "scheduled" and has_pending:
                    planned_inconsistent.append((order, operations))
            elif order.order_type == "production":
                if order.status == "scheduled" and all_scheduled:
                    production_correct.append((order, operations))
        
        print(f"1. 计划订单（正确状态）：订单status=created，工序status=pending")
        print(f"   数量：{len(planned_correct)} 个")
        print()
        
        print(f"2. 计划订单（不一致状态）：订单status=scheduled，工序status=pending")
        print(f"   数量：{len(planned_inconsistent)} 个")
        if planned_inconsistent:
            print(f"   示例订单：")
            for order, ops in planned_inconsistent[:3]:
                print(f"   - {order.order_number}: 订单status={order.status}, 工序都是pending")
        print()
        
        print(f"3. 生产订单（正确状态）：订单status=scheduled，工序status=scheduled")
        print(f"   数量：{len(production_correct)} 个")
        print()
        
        print("=" * 100)
        print("KPI统计分析")
        print("=" * 100)
        print()
        
        # 当前KPI统计逻辑
        current_kpi_count = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.status == models.OrderStatus.SCHEDULED.value
        ).count()
        
        print(f"当前KPI统计逻辑（只看订单status=scheduled）：")
        print(f"  已排程订单数 = {current_kpi_count}")
        print()
        
        # 正确的KPI统计逻辑
        correct_scheduled_count = 0
        for order in all_orders:
            operations = db.query(models.Operation).filter(
                models.Operation.order_id == order.id
            ).all()
            
            if operations:
                has_pending = any(op.status == "pending" for op in operations)
                if not has_pending and order.status == "scheduled":
                    correct_scheduled_count += 1
        
        print(f"正确的KPI统计逻辑（订单scheduled且无pending工序）：")
        print(f"  已排程订单数 = {correct_scheduled_count}")
        print()
        
        print("=" * 100)
        print("问题总结")
        print("=" * 100)
        print()
        print(f"发现 {len(planned_inconsistent)} 个计划订单存在数据不一致：")
        print(f"  - 订单级别：status = 'scheduled'（已排程）")
        print(f"  - 工序级别：status = 'pending'（待排程）")
        print()
        print("这导致：")
        print(f"  1. KPI统计认为有 {current_kpi_count} 个已排程订单")
        print(f"  2. 前端显示只有 {correct_scheduled_count} 个已排程订单")
        print(f"  3. 差异：{current_kpi_count - correct_scheduled_count} 个")
        print()
        print("原因分析：")
        print("  这些计划订单可能是：")
        print("  1. 由于之前的修改（将生产订单默认状态改为scheduled）")
        print("  2. 数据初始化时的逻辑问题")
        print("  3. 某些操作导致订单status被错误更新为scheduled")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_detailed_status()
