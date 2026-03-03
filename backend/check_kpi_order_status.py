"""
检查订单状态分布，诊断KPI统计问题
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal
from app import models

def check_order_status():
    db = SessionLocal()
    
    try:
        # 获取所有订单
        all_orders = db.query(models.ProductionOrder).all()
        
        print("=" * 80)
        print("订单状态分布检查")
        print("=" * 80)
        print()
        
        # 按订单类型和状态分组统计
        print("1. 按订单类型和状态分组：")
        print("-" * 80)
        
        planned_created = 0
        planned_scheduled = 0
        production_created = 0
        production_scheduled = 0
        production_with_confirmed = 0
        
        for order in all_orders:
            if order.order_type == "planned":
                if order.status == "created":
                    planned_created += 1
                elif order.status == "scheduled":
                    planned_scheduled += 1
            elif order.order_type == "production":
                if order.status == "created":
                    production_created += 1
                elif order.status == "scheduled":
                    production_scheduled += 1
                if order.confirmed_end:
                    production_with_confirmed += 1
        
        print(f"计划订单 - 待排程(created): {planned_created}")
        print(f"计划订单 - 已排程(scheduled): {planned_scheduled}")
        print(f"生产订单 - 待排程(created): {production_created}")
        print(f"生产订单 - 已排程(scheduled): {production_scheduled}")
        print(f"生产订单 - 有confirmed_end: {production_with_confirmed}")
        print()
        
        # KPI计算逻辑验证
        print("2. KPI '已排程订单' 统计逻辑验证：")
        print("-" * 80)
        
        # 按照代码逻辑：status=SCHEDULED 或 (order_type=production AND confirmed_end!=None)
        planned_scheduled_list = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.status == models.OrderStatus.SCHEDULED.value
        ).all()
        
        production_with_confirmed_list = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.order_type == models.OrderType.PRODUCTION.value,
            models.ProductionOrder.confirmed_end != None
        ).all()
        
        all_scheduled_ids = set(o.id for o in planned_scheduled_list)
        for o in production_with_confirmed_list:
            all_scheduled_ids.add(o.id)
        
        scheduled_count = len(all_scheduled_ids)
        
        print(f"status=SCHEDULED 的订单数: {len(planned_scheduled_list)}")
        print(f"order_type=production 且有 confirmed_end 的订单数: {len(production_with_confirmed_list)}")
        print(f"合并去重后的已排程订单数: {scheduled_count}")
        print()
        
        # 详细列出所有 status=SCHEDULED 的订单
        print("3. 所有 status='scheduled' 的订单详情：")
        print("-" * 80)
        
        for order in planned_scheduled_list:
            order_type_label = "生产订单" if order.order_type == "production" else "计划订单"
            
            # 检查工序状态
            operations = db.query(models.Operation).filter(
                models.Operation.order_id == order.id
            ).all()
            
            has_pending = any(op.status == "pending" for op in operations)
            all_scheduled = all(op.status == "scheduled" for op in operations)
            
            op_status_summary = ""
            if has_pending:
                op_status_summary = "有待排程工序"
            elif all_scheduled:
                op_status_summary = "全部工序已排程"
            else:
                op_status_summary = "工序状态混合"
            
            print(f"{order_type_label} {order.order_number}:")
            print(f"  订单状态: {order.status}")
            print(f"  工序数量: {len(operations)}")
            print(f"  工序状态: {op_status_summary}")
            
            if order.order_type == "production":
                print(f"  confirmed_end: {order.confirmed_end}")
            
            print()
        
        # 显示前端可能显示为"待排程"的订单
        print("4. 前端显示逻辑分析（有pending工序的订单会显示为待排程）：")
        print("-" * 80)
        
        display_as_created = 0
        display_as_scheduled = 0
        
        for order in all_orders:
            operations = db.query(models.Operation).filter(
                models.Operation.order_id == order.id
            ).all()
            
            has_pending = any(op.status == "pending" for op in operations)
            
            # 前端显示逻辑
            display_status = "created" if has_pending else order.status
            
            if display_status == "created":
                display_as_created += 1
            elif display_status == "scheduled":
                display_as_scheduled += 1
        
        print(f"前端显示为 '待排程' 的订单数: {display_as_created}")
        print(f"前端显示为 '已排程' 的订单数: {display_as_scheduled}")
        print()
        
        print("=" * 80)
        print("总结：")
        print("=" * 80)
        print(f"数据库总订单数: {len(all_orders)}")
        print(f"KPI统计的已排程订单数: {scheduled_count}")
        print(f"前端显示为待排程的订单数: {display_as_created}")
        print()
        
        if scheduled_count != display_as_scheduled:
            print("⚠️ 发现问题：")
            print(f"  KPI统计的已排程订单数({scheduled_count}) 与 前端显示的已排程订单数({display_as_scheduled}) 不一致")
            print()
            print("原因分析：")
            print("  KPI统计基于订单的 status 字段")
            print("  前端显示基于工序的 status 字段（有pending工序则显示为待排程）")
            print("  可能存在：订单status=scheduled，但工序status=pending 的情况")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_order_status()
